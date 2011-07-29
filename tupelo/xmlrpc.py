#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import time
import xmlrpclib
import players
import rpc
from common import GameState, CardSet, GameError, RuleError, ProtocolError
from events import EventList, CardPlayedEvent, MessageEvent, TrickPlayedEvent, TurnEvent, StateChangedEvent

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
        elif isinstance(event, StateChangedEvent):
            self.game_state.update(event.game_state)
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
        self.server.player.quit(player_id)

    @fault2error
    def register_player(self, player):
        player.controller = self
        player.id = self.server.player.register(rpc.rpc_encode(player))

    @fault2error
    def start_game_with_bots(self):
        return self.server.game.start_with_bots(self.game_id)

