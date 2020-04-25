#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

from typing import Optional
from enum import IntEnum
from .rpc import RPCSerializable, rpc_encode, rpc_decode

class EventType(IntEnum):
    NONE = 0
    CARD_PLAYED = 1
    MESSAGE = 2
    TRICK_PLAYED = 3
    TURN = 4
    STATE_CHANGED = 5

    def rpc_encode(self):
        return int(self)


class Event(RPCSerializable):
    """
    Class for events.
    """
    type = EventType.NONE
    rpc_attrs = ('type',)

    @classmethod
    def rpc_decode(cls, rpcobj):
        """
        Decode an rpc object into an Event instance.
        """
        for subcls in cls.__subclasses__():
            if getattr(subcls, 'type') == rpcobj['type']:
                return rpc_decode(subcls, rpcobj)

        return cls.rpc_decode_simple(rpcobj)


class CardPlayedEvent(Event):
    """
    A card has been played.
    """
    type = EventType.CARD_PLAYED
    rpc_attrs = Event.rpc_attrs + ('player:Player', 'card:Card', 'game_state:GameState')

    def __init__(self, player=None, card=None, game_state=None):
        self.player = player
        self.card = card
        self.game_state = game_state


class MessageEvent(Event):
    """
    A message.
    """
    type = EventType.MESSAGE
    rpc_attrs = Event.rpc_attrs + ('sender', 'message')

    def __init__(self, sender: Optional[str] = None, message: Optional[str] = None):
        self.sender = sender
        self.message = message


class TrickPlayedEvent(Event):
    """
    A trick (tikki/kasa) has been played.
    """
    type = EventType.TRICK_PLAYED
    rpc_attrs = Event.rpc_attrs + ('player:Player', 'game_state:GameState')

    def __init__(self, player=None, game_state=None):
        self.player = player
        self.game_state = game_state


class TurnEvent(Event):
    """
    It is the player's turn to do something.
    """
    type = EventType.TURN
    rpc_attrs = Event.rpc_attrs + ('game_state:GameState',)

    def __init__(self, game_state=None):
        self.game_state = game_state


class StateChangedEvent(Event):
    """
    Game state has changed.
    """
    type = EventType.STATE_CHANGED
    rpc_attrs = Event.rpc_attrs + ('game_state:GameState',)

    def __init__(self, game_state=None):
        self.game_state = game_state


class EventList(list, RPCSerializable):
    """
    Class for event lists.
    """
    def rpc_encode(self):
        return [rpc_encode(event) for event in self]

    @classmethod
    def rpc_decode(cls, rpcobj):
        elist = cls()
        for event in rpcobj:
            elist.append(rpc_decode(Event, event))
        return elist

