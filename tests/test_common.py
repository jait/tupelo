#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import unittest
import rpc
import common
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
        cs = common.CardSet
        deck = cs.new_full_deck()
        self.assert_(len(deck) == 52)
        for suit in common.ALL_SUITS:
            cards = deck.get_cards(suit=common.HEART)
            self.assert_(len(cards) == 13)

        for i in range(2, 15):
            cards = deck.get_cards(value=i)
            self.assert_(len(cards) == 4)


if __name__ == '__main__':
    unittest.main()
