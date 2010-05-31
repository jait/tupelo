#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import time
import xmlrpclib
import players
import rpc
from common import GameState, Card, CardSet, GameError, RuleError 
import game

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
        self.game.player_quit(self._get_player(player_id))
        # without allow_none, XMLRPC methods must always return something
        return True

    @error2fault
    def get_state(self, player_id):
        response = {}
        response['game_state'] = rpc.rpc_encode(self.game.state)
        response['hand'] = rpc.rpc_encode(self._get_player(player_id).hand)
        return response

    @error2fault
    def get_messages(self, player_id):
        return self._get_player(player_id).pop_messages()

    @error2fault
    def get_messages_since(self, player_id, last_msg_id):
        return self._get_player(player_id).get_messages_since(last_msg_id)
         
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
        print 'Player %s ' % player
        self.game.play_card(player, rpc.rpc_decode(Card, card))
        return True


class RPCProxyPlayer(players.Player):
    """
    Server-side class for remote/RPC players.
    """
    def __init__(self, name):
        players.Player.__init__(self, name)
        self.messages = []
        self.msg_id = 0

    def vote(self):
        """
        Unused method.
        """
        pass

    def play_card(self):
        """
        Unused method.
        """
        pass
           
    def card_played(self, player, card, game_state):
        # TODO: do we need a real event for this?
        msg = '%s played %s ' % (player, card)
        self.send_message('', msg)

    def send_message(self, sender, msg):
        """
        """
        self.messages.insert(0, (sender, msg))
        # TODO: rollover?
        self.msg_id += 1

    def pop_message(self):
        """
        """
        return self.messages.pop()

    def pop_messages(self):
        msgs = []
        # TODO: race conditions?
        while len(self.messages) > 0:
            msgs.append(self.pop_message())

        return msgs

    def get_messages_since(self, msg_id):
        """
        """
        amount = self.msg_id - msg_id
        if amount < 0 or amount > len(self.messages):
            raise IndexError()
        ret = self.messages[:amount]
        self.messages = ret
        return ret

class XMLRPCCliPlayer(players.CliPlayer):
    """
    XML-RPC command line interface human player.
    """
    def __init__(self, player_name):
        players.CliPlayer.__init__(self, player_name)
        self.game_state = None
        self.hand = None

    def wait_for_turn(self):
        """
        Wait for this player's turn.
        """
        while True:

            time.sleep(0.5)

            if self.controller is not None:
                state = self.controller.get_state(self.id)
                self.game_state = state['game_state']
                self.hand = state['hand']
                messages = self.controller.get_messages(self.id)
                for msg in messages:
                    print '%s: %s' % (msg[0], msg[1])

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
    def get_messages(self, player_id):
        return self.server.get_messages(player_id)

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

