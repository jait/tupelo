#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import random
import copy
import uuid
import base64
from functools import wraps
from . import rpc

# game mode
NOLO = 0
RAMI = 1

TURN_NONE = -1

def simple_decorator(decorator):
    """This decorator can be used to turn simple functions
    into well-behaved decorators, so long as the decorators
    are fairly simple. If a decorator expects a function and
    returns a function (no descriptors), and if it doesn't
    modify function attributes or docstring, then it is
    eligible to use this. Simply apply @simple_decorator to
    your decorator and it will automatically preserve the
    docstring and function attributes of functions to which
    it is applied."""
    def new_decorator(func):
        decf = decorator(func)
        decf.__name__ = func.__name__
        decf.__doc__ = func.__doc__
        decf.__dict__.update(func.__dict__)
        return decf
    # Now a few lines needed to make simple_decorator itself
    # be a well-behaved decorator.
    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    return new_decorator

@simple_decorator
def traced(func):
    """
    A decorator for tracing func calls.
    """
    def wrapper(*args, **kwargs):
        print(("DEBUG: entering %s()" % func.__name__))
        retval = func(*args, **kwargs)
        return retval

    return wrapper

def synchronized_method(lock_name):
    """
    Simple synchronization decorator for methods.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            lock = self.__getattribute__(lock_name)
            lock.acquire()
            try:
                return func(self, *args, **kwargs)
            finally:
                lock.release()

        return wrapper

    return decorator

def short_uuid():
    """
    Generate a short, random unique ID.

    Returns a string (base64 encoded UUID).
    """
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode().replace('=', '')


class TupeloException(Exception):
    """
    Base class for new exceptions.
    """
    def __init__(self, message=None):
        self.message = message


class GameError(TupeloException):
    """
    Generic error class for game errors.
    """
    rpc_code = 1


class RuleError(TupeloException):
    """
    Error for breaking the game rules.
    """
    rpc_code = 2


class ProtocolError(TupeloException):
    """
    Error for problems in using the RPC protocol.
    """
    rpc_code = 3


class UserQuit(GameError):
    """
    Exception for indicating that user quits the game.
    """
    pass


class Suit():
    """
    Class for suits.
    """
    def __init__(self, value, name, char=''):
        self.name = name
        self.value = value
        self.char = char

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return self.value != other.value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

    def rpc_encode(self):
        return self.value

    @classmethod
    def rpc_decode(cls, value):
        return _get_suit(value)

    def __str__(self):
        """
        Get the 'unofficial' string representation.
        """
        return self.name

HEART = Suit(3, 'hearts', '\u2665')
CLUB = Suit(2, 'clubs', '\u2663')
DIAMOND = Suit(1, 'diamonds', '\u2666')
SPADE = Suit(0, 'spades', '\u2660')

ALL_SUITS = [SPADE, DIAMOND, CLUB, HEART]

def _get_suit(value: int) -> Suit:
    try:
        return ALL_SUITS[value]
    except IndexError:
        raise ValueError("Suit not found")

class Card(rpc.RPCSerializable):
    """
    Class that represents a single card.
    """
    _chars = {11:'J', 12:'Q', 13:'K', 14:'A'}
    rpc_attrs = ('suit', 'value', 'played_by')

    def __init__(self, suit: Suit, value: int):
        super().__init__()
        self.suit = suit
        self.value = value
        self.potential_owners = list(range(0, 4))
        self.played_by = None

    @classmethod
    def rpc_decode(cls, rpcobj) -> 'Card':
        card = Card(Suit.rpc_decode(rpcobj['suit']), rpcobj['value'])
        if 'played_by' in rpcobj:
            card.played_by = rpcobj['played_by']

        return card

    def __eq__(self, other):
        return self.suit == other.suit and self.value == other.value

    def __ne__(self, other):
        return self.suit != other.suit or self.value != other.value

    def __lt__(self, other):
        return self._cmp_value < other._cmp_value

    def __le__(self, other):
        return self._cmp_value <= other._cmp_value

    def __gt__(self, other):
        return self._cmp_value > other._cmp_value

    def __ge__(self, other):
        return self._cmp_value >= other._cmp_value

    def __repr__(self):
        """
        Get the official string representation of the object.
        """
        return f'<Card: {self.value} of {self.suit.name}>'

    @property
    def _cmp_value(self) -> int:
        """Get the integer value that can be used for comparing and sorting cards."""
        return self.suit.value * 13 + self.value

    def __str__(self):
        return '%s%s' % (self.char, self.suit.char)

    @property
    def char(self):
        """
        Get the character corresponding to the card value.
        """
        if self.value in self._chars:
            return self._chars[self.value]
        return str(self.value)


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
            if 'suit' in kwargs and card.suit != kwargs['suit']:
                continue

            if 'value' in kwargs and card.value != kwargs['value']:
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

        if 'roof' in kwargs:
            roof = kwargs['roof']

        if 'floor' in kwargs:
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

        if 'roof' in kwargs:
            roof = kwargs['roof']

        if 'floor' in kwargs:
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
    rpc_attrs = ('status', 'mode', 'table:CardSet', 'score', 'tricks', 'turn',
            'turn_id')

    # statuses
    OPEN = 0
    VOTING = 1
    ONGOING = 2
    STOPPED = 3

    def __init__(self):
        super().__init__()
        self.status = GameState.OPEN
        self.mode = NOLO
        self.table = CardSet()
        self.score = [0, 0]
        self.tricks = [0, 0]
        self.rami_chosen_by = None # Player
        self.turn = 0
        self.turn_id = 0
        self.dealer = 0

    def update(self, new_state):
        """
        Update the state from a new state object.
        """
        for attr in self.__dict__:
            if hasattr(new_state, attr):
                setattr(self, attr, getattr(new_state, attr))

    def next_in_turn(self, thenext=None):
        """
        Set the next player in turn.
        """
        if thenext is None:
            self.turn = (self.turn + 1) % 4
        else:
            self.turn = (thenext) % 4

    def __str__(self):
        statusstr = {GameState.OPEN: 'OPEN', GameState.STOPPED: 'STOPPED',
                GameState.VOTING: 'VOTING', GameState.ONGOING: 'ONGOING'}
        modestr = {NOLO: 'NOLO', RAMI: 'RAMI'}
        return "state: %s, mode: %s, score: %s, tricks: %s, dealer: %d" % \
                (statusstr[self.status], modestr[self.mode], str(self.score),
                        str(self.tricks), self.dealer)

