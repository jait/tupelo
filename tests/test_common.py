#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import unittest
import rpc
import common
from common import Card, CardSet
import copy

class TestCommon(unittest.TestCase):

    def testSuitGlobals(self):
        self.assert_(common.HEART > common.CLUB)
        self.assert_(common.CLUB > common.DIAMOND)
        self.assert_(common.DIAMOND > common.SPADE)

    def testSuitRPC(self):
        heart = common.HEART
        encoded = rpc.rpc_encode(heart)
        decoded = rpc.rpc_decode(common.Suit, encoded)
        self.assert_(isinstance(decoded, common.Suit))
        self.assertEqual(heart.value, decoded.value)
        self.assertEqual(heart.name, decoded.name)

    def testCardSet(self):
        deck = CardSet.new_full_deck()
        self.assert_(len(deck) == 52)
        for suit in common.ALL_SUITS:
            cards = deck.get_cards(suit=common.HEART)
            self.assert_(len(cards) == 13)

        for i in range(2, 15):
            cards = deck.get_cards(value=i)
            self.assert_(len(cards) == 4)

        deck.clear()
        self.assert_(len(deck) == 0)

    def testCardSetHighest(self):
        cs = CardSet()
        cs.append(Card(common.HEART, 5))
        cs.append(Card(common.HEART, 7))
        cs.append(Card(common.HEART, 11))
        hi = cs.get_highest()
        self.assertEqual(hi.value, 11)
        hi = cs.get_highest(roof=9)
        self.assertEqual(hi.value, 7)
        hi = cs.get_highest(roof=7)
        self.assertEqual(hi.value, 7)
        hi = cs.get_highest(roof=2)
        self.assert_(hi is None)
        hi = cs.get_highest(floor=12)
        self.assert_(hi is None)

    def testCardSetLowest(self):
        cs = CardSet()
        cs.append(Card(common.HEART, 5))
        cs.append(Card(common.HEART, 7))
        cs.append(Card(common.HEART, 11))
        lo = cs.get_lowest()
        self.assertEqual(lo.value, 5)
        lo = cs.get_lowest(floor=9)
        self.assertEqual(lo.value, 11)
        lo = cs.get_lowest(floor=7)
        self.assertEqual(lo.value, 7)
        lo = cs.get_lowest(floor=12)
        self.assert_(lo is None)
        lo = cs.get_lowest(roof=2)
        self.assert_(lo is None)


if __name__ == '__main__':
    unittest.main()
