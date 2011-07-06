#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import time
import xmlrpclib
import players
import rpc
from common import GameState, Card, CardSet, GameError, RuleError, ProtocolError
from events import EventList, CardPlayedEvent, MessageEvent, TrickPlayedEvent, TurnEvent
import Queue
from game import GameController
import copy

DEFAULT_PORT = 8052

def error2fault(fn):
    """
    Catch known exceptions and translate them to 
    XML-RPC faults.
    """
    def catcher(*args):
        try:
            return fn(*args)
        except GameError, error:
            raise xmlrpclib.Fault(GameError.rpc_code, str(error))
        except RuleError, error:
            raise xmlrpclib.Fault(RuleError.rpc_code, str(error))
        except ProtocolError, error:
            raise xmlrpclib.Fault(ProtocolError.rpc_code, str(error))
    return catcher

def fault2error(fn):
    """
    Catch known XML-RPC faults and translate them to 
    custom exceptions.
    """
    def catcher(*args):
        try:
            return fn(*args)
        except xmlrpclib.Fault, error:
            error_classes = (GameError, RuleError, ProtocolError)
            for klass in error_classes:
                if error.faultCode == klass.rpc_code:
                    raise klass(error.faultString)

            raise error

    return catcher

class TupeloXMLRPCInterface(object):
    """
    The RPC interface for the tupelo server.
    """

    def __init__(self):
        super(TupeloXMLRPCInterface, self).__init__()
        self.players = []
        self.games = []
        self.methods = [f for f in dir(self) if not f.startswith('_')
                and callable(getattr(self, f))]

    def _get_player(self, player_id):
        """
        Get player by id.
        """
        for plr in self.players:
            if plr.id == player_id:
                return plr

        raise GameError('Player %d does not exist' % player_id)

    def _get_game(self, game_id):
        try:
            return self.games[game_id]
        except IndexError:
            raise GameError('Game %d does not exist' % game_id)

    def echo(self, test):
        return test

    @error2fault
    def _dispatch(self, method, params):
        realname = method.replace('.', '_')
        if realname in self.methods:
            func = getattr(self, realname)
            return func(*params)

        raise ProtocolError('Method "%s" is not supported' % method)

    def register_player(self, player):
        """
        Register a new player to the server.

        Return the player id.
        """
        player = rpc.rpc_decode(RPCProxyPlayer, player)
        self.players.append(player)
        player.id = self.players.index(player)
        return player.id

    def list_games(self):
        """
        List all games on server.

        Return a dict: game ID => list of player IDs
        """
        response = {}
        for game in self.games:
            response[game.id] = [player.id for player in game.players]

        return response

    def game_create(self, player_id):
        """
        Create a new game and enter it.

        Return the game id.
        """
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

        Return True
        """
        game = self._get_game(game_id)
        player = self._get_player(player_id)
        game.register_player(player)
        player.game = game
        return True

    def player_quit(self, player_id):
        """
        Player quits.
        """
        # leave the game. Does not necessarily end the game.
        player = self._get_player(player_id)
        game = player.game
        if game:
            game.player_leave(player_id)
            player.game = None

        # if the game was terminated we need to kill the old game instance
        if len(game.players) == 0:
            self.games.remove(game)

        # without allow_none, XMLRPC methods must always return something
        return True

    def game_get_state(self, game_id, player_id):
        game = self._get_game(game_id)
        response = {}
        response['game_state'] = rpc.rpc_encode(game.state)
        response['hand'] = rpc.rpc_encode(self._get_player(player_id).hand)
        return response

    def get_events(self, player_id):
        return rpc.rpc_encode(self._get_player(player_id).pop_events())
         
    def game_start(self, game_id):
        game = self._get_game(game_id)
        game.start_game()
        return True

    def game_start_with_bots(self, game_id):
        game = self._get_game(game_id)
        i = 1
        while len(game.players) < 4:
            game.register_player(players.DummyBotPlayer('Robotti %d' % i))
            i += 1

        return self.game_start(game_id)

    def game_play_card(self, game_id, player_id, card):
        game = self._get_game(game_id)
        player = self._get_player(player_id)
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


class XMLRPCCliPlayer(players.CliPlayer):
    """
    XML-RPC command line interface human player.
    """
    def __init__(self, player_name):
        players.CliPlayer.__init__(self, player_name)
        self.game_state = GameState()
        self.hand = None

    def handle_event(self, event):
        if isinstance(event, CardPlayedEvent):
            self.card_played(event.player, event.card, event.game_state)
        elif isinstance(event, MessageEvent):
            self.send_message(event.sender, event.message)
        elif isinstance(event, TrickPlayedEvent):
            self.trick_played(event.player, event.game_state)
        elif isinstance(event, TurnEvent):
            self.game_state.update(event.game_state)
            state = self.controller.get_state(self.id)
            self.hand = state['hand']
            self.game_state.update(state['game_state'])
        else:
            print "unknown event: %s" % event

    def wait_for_turn(self):
        """
        Wait for this player's turn.
        """
        while True:

            time.sleep(0.5)

            if self.controller is not None:
                events = self.controller.get_events(self.id)
                for event in events:
                    self.handle_event(event)

            if self.game_state.turn_id == self.id:
                break


class XMLRPCProxyController(object):
    """
    Client-side proxy object for the server/GameController.
    """
    def __init__(self, server_uri):
        super(XMLRPCProxyController, self).__init__()
        if not server_uri.startswith('http://') and \
            not server_uri.startswith('https://'):
            server_uri = 'http://' + server_uri

        self.server = xmlrpclib.ServerProxy(server_uri)
        self.game_id = None

    @fault2error
    def play_card(self, player, card):
        self.server.game.play_card(self.game_id, player.id, rpc.rpc_encode(card))

    @fault2error
    def get_events(self, player_id):
        return rpc.rpc_decode(EventList, self.server.get_events(player_id))

    @fault2error
    def get_state(self, player_id):
        state = self.server.game.get_state(self.game_id, player_id)
        state['game_state'] = rpc.rpc_decode(GameState, state['game_state'])
        state['hand'] = rpc.rpc_decode(CardSet, state['hand'])
        return state

    @fault2error
    def player_quit(self, player_id):
        self.server.player_quit(player_id)

    @fault2error
    def register_player(self, player):
        player.controller = self
        player.id = self.server.register_player(rpc.rpc_encode(player))

    @fault2error
    def start_game_with_bots(self):
        return self.server.game.start_with_bots(self.game_id)

