#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import players
import rpc
from common import Card, GameError, RuleError, ProtocolError, traced
from game import GameController
from events import EventList, CardPlayedEvent, MessageEvent, TrickPlayedEvent, TurnEvent, StateChangedEvent
import sys
import copy
import Queue
import SimpleXMLRPCServer
import xmlrpc
import traceback
import inspect
import json
import urlparse
try:
    from urlparse import parse_qs
except:
    from cgi import parse_qs


DEFAULT_PORT = 8052


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
            response = self.server.json_dispatch(self.path)
        except ProtocolError, err:
            self.report_404()
            return
        except (GameError, RuleError), err:
            traceback.print_exception(*sys.exc_info())
            self.send_response(403) # forbidden
            response_obj = {'code': err.rpc_code,
                'message': str(err)}
            response = json.dumps(response_obj)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()

            self.wfile.write(response)
            # shut down the connection
            self.wfile.flush()
            self.connection.shutdown(1)
        except Exception, err:
            traceback.print_exception(*sys.exc_info())
            self.send_response(500)
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", str(len(response)))

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

    def json_dispatch(self, qstring):
        """
        Dispatch a JSON method call to the interface instance.
        """
        method, params = self._json_parse_qstring(qstring)
        if not method:
            raise ProtocolError('No such method')

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
                methods[mname] = inspect.getargspec(func)[0]

        return methods

    def _get_player(self, player_id):
        """
        Get player by id.
        """
        for plr in self.players:
            if plr.id == player_id:
                return plr

        raise GameError('Player %d does not exist' % player_id)

    def _get_game(self, game_id):
        """
        Get game by id or raise an error.
        """
        try:
            return self.games[game_id]
        except IndexError:
            raise GameError('Game %d does not exist' % game_id)

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

            return func(**kwparams)

        raise ProtocolError('Method "%s" is not supported' % method)

    def player_register(self, player):
        """
        Register a new player to the server.

        Return the player id.
        """
        player = rpc.rpc_decode(RPCProxyPlayer, player)
        self.players.append(player)
        player.id = self.players.index(player)
        return player.id

    def player_quit(self, player_id):
        """
        Player quits.
        """
        # leave the game. Does not necessarily end the game.
        player_id = int(player_id)
        player = self._get_player(player_id)
        game = player.game
        if game:
            game.player_leave(player_id)
            player.game = None
            # if the game was terminated we need to kill the old game instance
            if len(game.players) == 0:
                self.games.remove(game)

        # without allow_none, XML-RPC methods must always return something
        return True

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

    def game_create(self, player_id):
        """
        Create a new game and enter it.

        Return the game id.
        """
        player_id = int(player_id)
        player = self._get_player(player_id)
        game = GameController()
        # TODO: slight chance of race
        self.games.append(game)
        game.id = self.games.index(game)
        self.game_enter(game.id, player.id)
        return game.id

    def game_enter(self, game_id, player_id):
        """
        Register a new player to the game.

        Return game ID
        """
        game = self._get_game(int(game_id))
        player = self._get_player(int(player_id))
        if player.game:
            raise GameError("Player is already in a game")

        game.register_player(player)
        player.game = game
        return game_id

    def game_get_state(self, game_id, player_id):
        """
        Get the state of a game for given player.
        """
        game = self._get_game(int(game_id))
        response = {}
        response['game_state'] = rpc.rpc_encode(game.state)
        response['hand'] = rpc.rpc_encode(self._get_player(int(player_id)).hand)
        return response

    def game_get_info(self, game_id):
        """
        Get the (static) information of a game.
        """
        game = self._get_game(int(game_id))
        return _game_get_rpc_info(game)

    def get_events(self, player_id):
        """
        Get the list of new events for given player.
        """
        return rpc.rpc_encode(self._get_player(int(player_id)).pop_events())

    def game_start(self, game_id):
        """
        Start a game.
        """
        game = self._get_game(int(game_id))
        game.start_game()
        return True

    def game_start_with_bots(self, game_id):
        """
        Start a game with bots.
        """
        game_id = int(game_id)
        game = self._get_game(game_id)
        i = 1
        while len(game.players) < 4:
            game.register_player(players.DummyBotPlayer('Robotti %d' % i))
            i += 1

        return self.game_start(game_id)

    def game_play_card(self, game_id, player_id, card):
        """
        Play one card in given game, by given player.
        """
        game = self._get_game(int(game_id))
        player = self._get_player(int(player_id))
        game.play_card(player, rpc.rpc_decode(Card, card))
        return True


class RPCProxyPlayer(players.ThreadedPlayer):
    """
    Server-side class for remote/RPC players.
    """
    def __init__(self, name):
        players.ThreadedPlayer.__init__(self, name)
        self.events = Queue.Queue()
        self.game = None

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

