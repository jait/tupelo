#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import unittest
from tupelo import rpc
from tupelo import common
from tupelo.common import Card, CardSet, smart_unicode, smart_str, TupeloException

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

    def testCardRPC(self):
        card = Card(common.HEART, 5)
        encoded = rpc.rpc_encode(card)
        self.assertFalse(isinstance(encoded, common.Card))
        decoded = rpc.rpc_decode(common.Card, encoded)
        self.assert_(isinstance(decoded, common.Card))
        self.assertEqual(card, decoded)

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

    def testGameStateRPC(self):
        gs = common.GameState()
        gs.table.append(Card(common.HEART, 5))
        encoded = rpc.rpc_encode(gs)
        gs2 = rpc.rpc_decode(common.GameState, encoded)
        self.assert_(isinstance(gs2, common.GameState))
        self.assert_(isinstance(gs2.table, gs.table.__class__))
        self.assertEqual(len(gs2.table), len(gs.table))

    def testSmartUnicode(self):
        self.assertEqual(smart_unicode('hello'), u'hello')
        self.assertEqual(smart_unicode(u'hello'), u'hello')
        self.assertEqual(smart_unicode('hellö'), u'hell\u00F6')
        self.assertEqual(smart_unicode(u'hell\u00F6'), u'hell\u00F6')
        self.assertEqual(smart_unicode(1), u'1')
        self.assertEqual(smart_unicode(u'\u2665'), u'\u2665')
        self.assertEqual(smart_unicode(TupeloException(u'hell\u00F6')), u'hell\u00F6')
        self.assertEqual(smart_unicode(TupeloException('hellö')), u'hell\u00F6')

    def testSmartStr(self):
        self.assertEqual(smart_str('hello'), 'hello')
        self.assertEqual(smart_str(u'hello'), 'hello')
        self.assertEqual(smart_str('hellö'), 'hellö')
        self.assertEqual(smart_str(u'hell\u00F6'), 'hellö')
        self.assertEqual(smart_str(1), '1')
        self.assertEqual(smart_str(u'\u2665'), '\xe2\x99\xa5')
        self.assertRaises(UnicodeEncodeError, lambda: smart_str(u'hellö', 'ascii'))
        self.assertEqual(smart_str(TupeloException(u'hellö')), 'hellö')
        self.assertEqual(smart_str(TupeloException('hellö')), 'hellö')


if __name__ == '__main__':
    unittest.main()
