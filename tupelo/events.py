#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import rpc
from players import Player
from common import Card, GameState

class Event(rpc.RPCSerializable):
    """
    Class for events.
    """
    type = 0
    rpc_attrs = ('type',)

    @classmethod
    def rpc_decode(cls, rpcobj):
        """
        Decode an rpc object into an Event instance.
        """
        instance = None
        for subcls in cls.__subclasses__():
            if getattr(subcls, 'type') == rpcobj['type']:
                return rpc.rpc_decode(subcls, rpcobj)

        return cls.rpc_decode_simple(rpcobj)


class CardPlayedEvent(Event):
    """
    A card has been played.
    """
    type = 1
    rpc_attrs = Event.rpc_attrs + ('player', 'card', 'game_state')

    def __init__(self, player=None, card=None, game_state=None):
       self.player = player
       self.card = card
       self.game_state = game_state

    @classmethod
    def rpc_decode(cls, rpcobj):
        instance = cls.rpc_decode_simple(rpcobj)
        if rpcobj.has_key('player'):
            instance.player = rpc.rpc_decode(Player, rpcobj['player'])

        if rpcobj.has_key('card'):
            instance.card = rpc.rpc_decode(Card, rpcobj['card'])

        if rpcobj.has_key('game_state'):
            instance.game_state = rpc.rpc_decode(GameState, rpcobj['game_state'])

        return instance


class MessageEvent(Event):
    """
    A message.
    """
    type = 2
    rpc_attrs = Event.rpc_attrs + ('sender', 'message')

    def __init__(self, sender=None, message=None):
        self.sender = sender
        self.message = message


class TrickPlayedEvent(Event):
    """
    A card has been played.
    """
    type = 3
    rpc_attrs = Event.rpc_attrs + ('player', 'game_state')

    def __init__(self, player=None, game_state=None):
       self.player = player
       self.game_state = game_state

    @classmethod
    def rpc_decode(cls, rpcobj):
        instance = cls.rpc_decode_simple(rpcobj)
        instance.player = rpc.rpc_decode(Player, rpcobj['player'])
        instance.game_state = rpc.rpc_decode(GameState, rpcobj['game_state'])
        return instance


class TurnEvent(Event):
    """
    It is the player's turn to do something.
    """
    type = 4
    rpc_attrs = Event.rpc_attrs + ('game_state',)

    def __init__(self, game_state=None):
       self.game_state = game_state

    @classmethod
    def rpc_decode(cls, rpcobj):
        instance = cls.rpc_decode_simple(rpcobj)
        instance.game_state = rpc.rpc_decode(GameState, rpcobj['game_state'])
        return instance


class EventList(list, rpc.RPCSerializable):
    """
    Class for event lists.
    """
    def rpc_encode(self):
        return [rpc.rpc_encode(event) for event in self]

    @classmethod
    def rpc_decode(cls, rpcobj):
        elist = cls()
        for event in rpcobj:
            elist.append(rpc.rpc_decode(Event, event))
        return elist

