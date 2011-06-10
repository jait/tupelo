#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import rpc


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
    rpc_attrs = Event.rpc_attrs + ('player:Player', 'card:Card', 'game_state:GameState')

    def __init__(self, player=None, card=None, game_state=None):
        self.player = player
        self.card = card
        self.game_state = game_state

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
    rpc_attrs = Event.rpc_attrs + ('player:Player', 'game_state:GameState')

    def __init__(self, player=None, game_state=None):
        self.player = player
        self.game_state = game_state


class TurnEvent(Event):
    """
    It is the player's turn to do something.
    """
    type = 4
    rpc_attrs = Event.rpc_attrs + ('game_state:GameState',)

    def __init__(self, game_state=None):
        self.game_state = game_state


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

