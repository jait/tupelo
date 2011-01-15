#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import random
import copy
import rpc

# game mode
NOLO = 0
RAMI = 1

# game state
STOPPED = 0
VOTING = 1
ONGOING = 2

TURN_NONE = -1


def traced(func):
    """
    A decorator for tracing func calls.
    """
    def wrapper(*args, **kwargs):
        print "DEBUG: entering %s()" % func.__name__
        retval = func(*args, **kwargs)
        return retval

    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__

    return wrapper


class GameError(Exception):
    """
    Generic error class for game errors.
    """
    rpc_code = 1


class RuleError(Exception):
    """
    Error for breaking the game rules.
    """
    rpc_code = 2


class UserQuit(GameError):
    """
    Exception for indicating that user quits the game.
    """
    pass


class Suit(object):
    """
    Class for suits.
    """
    def __init__(self, value, name, char=''):
        self.name = name
        self.value = value
        self.char = char

    def __cmp__(self, other):
        return cmp(self.value, other.value)

    def rpc_encode(self):
        return self.value

    @classmethod
    def rpc_decode(cls, value):
        return _get_suit(value)

HEART = Suit(3, 'hearts', u'\u2665')
CLUB = Suit(2, 'clubs', u'\u2663')
DIAMOND = Suit(1, 'diamonds', u'\u2666')
SPADE = Suit(0, 'spades', u'\u2660')

ALL_SUITS = [HEART, CLUB, DIAMOND, SPADE]

def _get_suit(value):
    for suit in ALL_SUITS:
        if suit.value == value:
            return suit

    return None
        
class Card(rpc.RPCSerializable):
    """
    Class that represents a single card.
    """
    _chars = {11:'J', 12:'Q', 13:'K', 14:'A'}
    rpc_attrs = ('suit', 'value', 'played_by')

    def __init__(self, suit, value):
        super(Card, self).__init__()
        self.suit = suit
        self.value = value
        self.potential_owners = range(0, 4)
        self.played_by = None

    @classmethod
    def rpc_decode(cls, rpcobj):
        card = Card(rpc.rpc_decode(Suit, rpcobj['suit']), rpcobj['value'])
        if rpcobj.has_key('played_by'):
            card.played_by = rpcobj['played_by']

        return card

    def __eq__(self, other):
        return self.suit == other.suit and self.value == other.value

    def __ne__(self, other):
        return self.suit != other.suit or self.value != other.value

    def __cmp__(self, other):
        suitcmp = cmp(self.suit, other.suit)
        if suitcmp != 0: 
            return suitcmp

        return cmp(self.value, other.value)

    def __repr__(self):
        """
        Get the 'official string representation of the object.
        """
        return '<Card: %s of %s>' % (self.value, self.suit.name)

    def __str__(self):
        """
        Get the 'unofficial' string representation.
        """
        return '%s%s' % (self.char, self.suit.char)

    @property
    def char(self):
        """
        Get the character corresponding to the card value.
        """
        if self._chars.has_key(self.value):
            return self._chars[self.value]
        return str(self.value)

    def get_char(self):
        """
        For compatibility.
        """
        return self.char


class CardSet(list, rpc.RPCSerializable):
    """
    A set of cards.
    """
    @staticmethod
    def new_full_deck():
        """
        Create a full deck of cards.
        """
        deck = CardSet()
        for suit in ALL_SUITS:
            for val in range(2, 15):
                deck.append(Card(suit, val))

        return deck

    def __sub__(self, other):
        """
        """
        result = copy.copy(self)
        for elem in other:
            try:
                result.remove(elem)
            except ValueError:
                continue
        return result

    def rpc_encode(self):
        return [rpc.rpc_encode(card) for card in self]

    @classmethod
    def rpc_decode(cls, rpcobj):
        cset = cls()
        for card in rpcobj:
            cset.append(rpc.rpc_decode(Card, card))
        return cset

    def get_cards(self, **kwargs):
        """
        Get cards from the set.

        Supported keyword args:
            - suit: get cards having the given suit
            - value: get cards having the given value
        """
        result = CardSet()
        for card in self:
            if kwargs.has_key('suit') and card.suit != kwargs['suit']:
                continue

            if kwargs.has_key('value') and card.value != kwargs['value']:
                continue

            result.append(card)
        return result

    def shuffle(self):
        """
        Shuffle the CardSet to a random order.
        """
        random.shuffle(self)

    def take(self, card):
        """
        Take a selected card from the set.
        """
        self.remove(card)
        return card

    def clear(self):
        """
        Clear this set.
        """
        del self[:]

    def deal(self, cardsets):
        """
        Deal this CardSet into cardsets.
        """
        while len(self) > 0:
            for cset in cardsets:
                try:
                    cset.append(self.pop(0))
                except IndexError:
                    break

    def get_highest(self, **kwargs):
        """
        Get the card with the highest value.
        """
        highest = None
        roof = None
        floor = None

        if kwargs.has_key('roof'):
            roof = kwargs['roof']

        if kwargs.has_key('floor'):
            floor = kwargs['floor']

        for card in self:
            if floor is not None and card.value < floor:
                continue
            if roof is not None and card.value > roof:
                continue
            if highest is None or card.value > highest.value:
                highest = card
                    
        return highest

    def get_lowest(self, **kwargs):
        """
        Get the card with the lowest value.
        """
        lowest = None
        roof = None
        floor = None

        if kwargs.has_key('roof'):
            roof = kwargs['roof']

        if kwargs.has_key('floor'):
            floor = kwargs['floor']

        for card in self:
            if floor is not None and card.value < floor:
                continue
            if roof is not None and card.value > roof:
                continue
            if lowest is None or card.value < lowest.value:
                lowest = card

        return lowest

class GameState(rpc.RPCSerializable):
    """
    State of a single game.
    """
    rpc_attrs = ('state', 'mode', 'table:CardSet', 'score', 'tricks', 'turn')

    def __init__(self):
        super(GameState, self).__init__()
        self.state = STOPPED
        self.mode = NOLO
        self.table = CardSet()
        self.score = [0, 0]
        self.tricks = [0, 0]
        self.rami_chosen_by = None
        self.turn = 0
        self.dealer = 0

    def update(self, new_state):
        """
        Update the state from a new state object.
        """
        for attr in self.__dict__:
            if hasattr(new_state, attr):
                setattr(self, attr, getattr(new_state, attr))

    def next_in_turn(self, next=None):
        """
        Set the next player in turn.
        """
        if next is None:
            self.turn = (self.turn + 1) % 4
        else:
            self.turn = (next) % 4

    def __str__(self):
        statestr = {STOPPED: 'STOPPED', VOTING: 'VOTING', ONGOING: 'ONGOING'}
        modestr = {NOLO: 'NOLO', RAMI: 'RAMI'}
        return "state: %s, mode: %s, score: %s, tricks: %s, dealer: %d" % \
                (statestr[self.state], modestr[self.mode], str(self.score),
                        str(self.tricks), self.dealer)

