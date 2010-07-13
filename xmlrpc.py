#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import time
import xmlrpclib
import players
import rpc
from common import GameState, Card, CardSet, GameError, RuleError
from events import EventList, CardPlayedEvent, MessageEvent, TrickPlayedEvent, TurnEvent
import Queue
import game
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
            if error.faultCode == GameError.rpc_code:
                raise GameError(error.faultString)
            elif error.faultCode == RuleError.rpc_code:
                raise RuleError(error.faultString)
            else:
                raise error

    return catcher
            
class TupeloXMLRPCInterface(object):
    """
    The RPC interface for the tupelo server.
    """

    def __init__(self):
        super(TupeloXMLRPCInterface, self).__init__()
        self.game = game.GameController()

    def _get_player(self, player_id):
        for player in self.game.players:
            if player.id == player_id: 
                return player
        return None

    def echo(self, test):
        return test

    @error2fault
    def register_player(self, player):
        """
        Register a new player to the game.

        Return the player id.
        """
        player = rpc.rpc_decode(RPCProxyPlayer, player)
        self.game.register_player(player)
        return player.id

    @error2fault
    def player_quit(self, player_id):
        """
        Player quits.
        """
        # leave the game but don't make the server quit
        self.game.player_leave(self._get_player(player_id))
        # without allow_none, XMLRPC methods must always return something
        return True

    @error2fault
    def get_state(self, player_id):
        response = {}
        response['game_state'] = rpc.rpc_encode(self.game.state)
        response['hand'] = rpc.rpc_encode(self._get_player(player_id).hand)
        return response

    @error2fault
    def get_events(self, player_id):
        return rpc.rpc_encode(self._get_player(player_id).pop_events())
         
    @error2fault
    def start_game(self):
        self.game.start_game()
        return True

    @error2fault
    def start_game_with_bots(self):
        i = 1
        while len(self.game.players) < 4:
            self.game.register_player(players.DummyBotPlayer('Robotti %d' % i))
            i += 1

        return self.start_game()

    @error2fault
    def play_card(self, player_id, card):
        player = self._get_player(player_id)
        self.game.play_card(player, rpc.rpc_decode(Card, card))
        return True


class RPCProxyPlayer(players.ThreadedPlayer):
    """
    Server-side class for remote/RPC players.
    """
    def __init__(self, name):
        players.ThreadedPlayer.__init__(self, name)
        self.events = Queue.Queue()

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
            #self.game_state.update(state['game_state'])
            self.hand = state['hand']
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

            if self.game_state.turn == self.id:
                break


class XMLRPCProxyController(object):
    """
    Client-side proxy object for the server/GameController.
    """
    def __init__(self, server_uri):
        super(XMLRPCProxyController, self).__init__()
        self.server = xmlrpclib.ServerProxy(server_uri)

    @fault2error
    def play_card(self, player, card):
        self.server.play_card(player.id, rpc.rpc_encode(card))

    @fault2error
    def get_events(self, player_id):
        return rpc.rpc_decode(EventList, self.server.get_events(player_id))

    @fault2error
    def get_state(self, player_id):
        state = self.server.get_state(player_id)
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
        return self.server.start_game_with_bots()

