#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import players
import rpc
from common import Card, GameError, RuleError, ProtocolError, traced, short_uuid, simple_decorator, GameState
from game import GameController
from events import EventList, CardPlayedEvent, MessageEvent, TrickPlayedEvent, TurnEvent, StateChangedEvent
import sys
import copy
import logging
import Queue
import SimpleXMLRPCServer
import xmlrpc
import traceback
import inspect
import json
import urlparse
import Cookie
try:
    from urlparse import parse_qs
except:
    from cgi import parse_qs


DEFAULT_PORT = 8052

VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_STRING = "%d.%d" % (VERSION_MAJOR, VERSION_MINOR)

def _log_exc(exception, level=logging.INFO):
    """
    Print the exception type and value string to log.
    """
    logging.log(level, "%s: %s", type(exception).__name__, str(exception))

@simple_decorator
def authenticated(fn):
    """
    Method decorator to verify that the client sent a valid authentication
    key.
    """
    def wrapper(self, akey, *args, **kwargs):
        self._ensure_auth(akey)
        try:
            retval = fn(self, *args, **kwargs)
        finally:
            self._clear_auth()

        return retval

    # copy argspec from wrapped function
    wrapper.argspec = inspect.getargspec(fn)
    # and add our extra arg
    wrapper.argspec.args.insert(0, 'akey')
    return wrapper

def _game_get_rpc_info(game):
    """
    Get RPC info for a GameController instance.
    TODO: does not belong here.
    """
    return [rpc.rpc_encode(player) for player in game.players]


class TupeloRequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
    """
    Custom request handler class to support ajax/json RPC for GET requests and XML-RPC for POST.
    """

    @traced
    def do_GET(self):
        try:
            response = self.server.json_dispatch(self.path, self.headers)
        except ProtocolError, err:
            self.report_404()
            return
        except (GameError, RuleError), err:
            _log_exc(err)
            self.send_response(403) # forbidden
            response_obj = {'code': err.rpc_code,
                'message': str(err)}
            response = json.dumps(response_obj)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", str(len(response)))
            self.send_header("X-Error-Code", str(err.rpc_code))
            self.send_header("X-Error-Message", str(err))
            self.end_headers()

            self.wfile.write(response)
            # shut down the connection
            self.wfile.flush()
            self.connection.shutdown(1)
        except Exception, err:
            traceback.print_exception(*sys.exc_info())
            _log_exc(err, logging.ERROR)
            self.send_response(500)
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", str(len(response)))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Pragma", "no-cache")

            self.end_headers()
            self.wfile.write(response)

            # shut down the connection
            self.wfile.flush()
            self.connection.shutdown(1)


class TupeloJSONDispatcher(object):
    """
    Simple JSON dispatcher mixin that calls the methods of "instance" member.
    """

    json_path_prefix = '/ajax/'

    def _json_parse_headers(self, headers):
        """
        Parse the HTTP headers and extract any params from them.
        """
        params = {}
        # we support just 'akey' cookie
        cookie = Cookie.SimpleCookie(headers.get('Cookie'))
        if cookie.has_key('akey'):
            params['akey'] = cookie['akey'].value

        return params

    def _json_parse_qstring(self, qstring):
        """
        Parse a query string into method and parameters.

        Return a tuple of (method_name, params).
        """
        parsed = urlparse.urlparse(qstring)
        path = parsed[2]
        params = parse_qs(parsed[4])
        # use only the first value of any given parameter
        for k, v in params.items():
            # try to decode a json parameter
            # if it fails, fall back to plain string
            try:
                params[k] = json.loads(v[0])
            except:
                params[k] = v[0]

        method = None
        if self.json_path_prefix:
            if path.startswith(self.json_path_prefix):
                method = path[len(self.json_path_prefix):].replace('/', '_')
        else:
            method = path.lstrip('/').replace('/', '_')

        return (method, params)

    def json_dispatch(self, qstring, headers):
        """
        Dispatch a JSON method call to the interface instance.
        """
        method, qs_params = self._json_parse_qstring(qstring)
        if not method:
            raise ProtocolError('No such method')

        # the querystring params override header params
        params = self._json_parse_headers(headers)
        params.update(qs_params)

        # ugly. here we are relying on the existence of
        # "instance" member from SimpleXMLRPCDispatcher
        return json.dumps(self.instance._json_dispatch(method, params))


class TupeloServer(SimpleXMLRPCServer.SimpleXMLRPCServer, TupeloJSONDispatcher):
    """
    Custom server class that combines XML-RPC and JSON servers.
    """

    def __init__(self, *args, **kwargs):
        nargs = (args[0:1] or (None,)) +  (TupeloRequestHandler,) +  args[2:]
        SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(self, *nargs, **kwargs)
        TupeloJSONDispatcher.__init__(self)
        rpciface = TupeloRPCInterface()
        self.register_instance(rpciface)

    def shutdown_games(self):
        """
        Shut down all the games running on this instance.
        """
        for game in self.instance.games:
            game.shutdown()


class TupeloRPCInterface(object):
    """
    The RPC interface for the tupelo server.
    """

    def __init__(self):
        super(TupeloRPCInterface, self).__init__()
        self.players = []
        self.games = []
        self.methods = self._get_methods()
        self.authenticated_player = None

    def _get_methods(self):
        """
        Get a list of RPC methods that this object supports.

        Return a dict of method_name => [argument names]
        """
        method_names = [f for f in dir(self) if not f.startswith('_')]
        methods = dict()
        for mname in method_names:
            func = getattr(self, mname)
            if callable(func):
                # check if it is a decorated method
                if hasattr(func, 'argspec'):
                    methods[mname] = func.argspec[0]
                else:
                    methods[mname] = inspect.getargspec(func)[0]

                # remove 'self' from signature
                if 'self' in methods[mname]:
                    methods[mname].remove('self')

        return methods

    def _get_player(self, player_id):
        """
        Get player by id.
        """
        for plr in self.players:
            if plr.id == player_id:
                return plr

        raise GameError('Player (ID %s) does not exist' % player_id)

    def _register_player(self, player):
        """
        Register a new player to the server (internal function).
        """
        # generate a (public) ID and (private) access token
        player.id = short_uuid()
        player.akey = short_uuid()
        self.players.append(player)
        return player.rpc_encode(private=True)

    def _ensure_auth(self, akey):
        """
        Check the given authentication key and set self.authenticated_player.

        Raises GameError if akey is not valid.
        """
        for plr in self.players:
            if plr.akey == akey:
                self.authenticated_player = plr
                return self.authenticated_player

        raise GameError("Invalid authentication key")

    def _clear_auth(self):
        """
        Clear info about the authenticated player.
        """
        self.authenticated_player = None

    def _get_game(self, game_id):
        """
        Get game by id or raise an error.
        """
        for game in self.games:
            if game.id == game_id:
                return game

        raise GameError('Game %s does not exist' % game_id)

    def echo(self, test):
        return test

    @xmlrpc.error2fault
    def _dispatch(self, method, params):
        """
        Dispatch an XML-RPC call.
        """
        realname = method.replace('.', '_')
        if realname in self.methods.keys():
            func = getattr(self, realname)
            return func(*params)

        raise ProtocolError('Method "%s" is not supported' % method)

    def _json_dispatch(self, method, kwparams):
        """
        Dispatch a json method call to method with kwparams.
        """
        if method in self.methods.keys():
            func = getattr(self, method)
            # strip out invalid params
            for k in kwparams.keys():
                if k not in self.methods[method]:
                    del kwparams[k]
            try:
                return func(**kwparams)
            except TypeError, err:
                raise ProtocolError(str(err))

        raise ProtocolError('Method "%s" is not supported' % method)

    ### PUBLIC METHODS

    def hello(self, akey=None):
        """
        Client says hello.

        Return a dict with server version and player/game info if the akey
        was valid.
        """
        response = {'version': VERSION_STRING}
        try:
            self._ensure_auth(akey)
        except:
            pass

        # is the akey valid?
        if self.authenticated_player is not None:
            plr = self.authenticated_player
            response['player'] = plr.rpc_encode(private=True)
            if plr.game:
                response['game'] = _game_get_rpc_info(plr.game)

        self._clear_auth()
        return response

    def player_register(self, player):
        """
        Register a new player to the server.

        Return the player id.
        """
        player = rpc.rpc_decode(RPCProxyPlayer, player)
        return self._register_player(player)

    @authenticated
    def player_quit(self):
        """
        Player quits.
        """
        player = self.authenticated_player
        game = player.game
        # leave the game. Does not necessarily end the game.
        if game:
            try:
                self.game_leave(self.authenticated_player.akey, game.id)
            except GameError:
                pass

        self.players.remove(player)
        # without allow_none, XML-RPC methods must always return something
        return True

    @authenticated
    def player_list(self):
        """
        List all players on server.
        """
        return [rpc.rpc_encode(player) for player in self.players]

    def game_list(self, state=None):
        """
        List all games on server that are in the given state.
        """
        response = {}
        if state is not None:
            state = int(state)

        # TODO: add game state, joinable yes/no, password?
        for game in self.games:
            if state is None or game.state.state == state:
                response[str(game.id)] = _game_get_rpc_info(game)

        return response

    @authenticated
    def game_create(self):
        """
        Create a new game and enter it.

        Return the game id.
        """
        player = self.authenticated_player
        game = GameController()
        # TODO: slight chance of race
        self.games.append(game)
        game.id = short_uuid()
        try:
            self.game_enter(self.authenticated_player.akey, game.id)
        except GameError:
            self.games.remove(game)
            raise

        return game.id

    @authenticated
    def game_enter(self, game_id):
        """
        Register a new player to the game.

        Return game ID
        """
        game = self._get_game(game_id)
        player = self.authenticated_player
        if player.game:
            raise GameError("Player is already in a game")

        game.register_player(player)
        player.game = game
        return game_id

    @authenticated
    def game_leave(self, game_id):
        """
        Leave the game. Does not necessarily end the game.
        """
        game = self._get_game(game_id)
        player = self.authenticated_player
        game.player_leave(player.id)
        player.game = None
        # if the game was terminated we need to kill the old game instance
        if len(game.players) == 0:
            self.games.remove(game)

        return True

    @authenticated
    def game_get_state(self, game_id):
        """
        Get the state of a game for given player.
        """
        game = self._get_game(game_id)
        response = {}
        response['game_state'] = rpc.rpc_encode(game.state)
        response['hand'] = rpc.rpc_encode(self.authenticated_player.hand)
        return response

    def game_get_info(self, game_id):
        """
        Get the (static) information of a game.
        """
        game = self._get_game(game_id)
        return _game_get_rpc_info(game)

    @authenticated
    def get_events(self):
        """
        Get the list of new events for given player.
        """
        return rpc.rpc_encode(self.authenticated_player.pop_events())

    @authenticated
    def game_start(self, game_id):
        """
        Start a game.
        """
        game = self._get_game(game_id)
        game.start_game()
        return True

    @authenticated
    def game_start_with_bots(self, game_id):
        """
        Start a game with bots.
        """
        game = self._get_game(game_id)
        i = 1
        while len(game.players) < 4:
            # register bots only to game so that we don't need to unregister them
            game.register_player(players.DummyBotPlayer('Robotti %d' % i))
            i += 1

        return self.game_start(self.authenticated_player.akey, game_id)

    @authenticated
    def game_play_card(self, game_id, card):
        """
        Play one card in given game, by given player.
        """
        game = self._get_game(game_id)
        player = self.authenticated_player
        game.play_card(player, rpc.rpc_decode(Card, card))
        return True


class RPCProxyPlayer(players.Player):
    """
    Server-side class for remote/RPC players.
    """
    def __init__(self, name):
        players.Player.__init__(self, name)
        self.events = Queue.Queue()
        self.game = None

    def rpc_encode(self, private=False):
        rpcobj = players.Player.rpc_encode(self)
        # don't encode the game object, just the ID
        if self.game:
            rpcobj['game_id'] = rpc.rpc_encode(self.game.id)

        if private:
            if hasattr(self, 'akey'):
                rpcobj['akey'] = self.akey

        return rpcobj

    def vote(self):
        self.play_card()

    def play_card(self):
        self.send_event(TurnEvent(copy.deepcopy(self.game_state)))

    def card_played(self, player, card, game_state):
        self.send_event(CardPlayedEvent(player, card, copy.deepcopy(game_state)))

    def trick_played(self, player, game_state):
        self.send_event(TrickPlayedEvent(player, copy.deepcopy(game_state)))

    def state_changed(self, game_state):
        self.send_event(StateChangedEvent(copy.deepcopy(game_state)))

    def send_message(self, sender, msg):
        self.send_event(MessageEvent(sender, msg))

    def send_event(self, event):
        self.events.put(event)

    def pop_events(self):
        eventlist = EventList()
        try:
            while True:
                eventlist.append(self.events.get_nowait())
        except Queue.Empty:
            pass

        return eventlist

    def act(self, controller, game_state):
        self.controller = controller
        self.game_state.update(game_state)
        if self.game_state.state == GameState.STOPPED:
            return
        elif self.game_state.state == GameState.VOTING:
            self.vote()
        elif self.game_state.state == GameState.ONGOING:
            self.play_card()
        else:
            logging.warning("Warning: unknown state %d", self.game_state.state)

