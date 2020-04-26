#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import unittest
from tupelo import rpc
from tupelo import common
from tupelo.common import Card, CardSet
import threading
import copy
import time

class SyncTester(object):

    def __init__(self):
        self.lock = threading.Lock()
        self.counter = 0

    @common.synchronized_method('lock')
    def sync(self):
        assert self.counter == 0, 'oops, @synchronized_method did not work. '\
            'counter is %d' % self.counter
        self.counter += 1
        time.sleep(1)
        assert self.counter == 1, 'oops, @synchronized_method did not work. '\
            'counter is %d' % self.counter
        time.sleep(1)
        self.counter -= 1
        assert self.counter == 0, 'oops, @synchronized_method did not work. '\
            'counter is %d' % self.counter
        return True


class TestCommon(unittest.TestCase):

    def testSuitGlobals(self):
        self.assertTrue(common.HEART > common.CLUB)
        self.assertTrue(common.CLUB > common.DIAMOND)
        self.assertTrue(common.DIAMOND > common.SPADE)

    def testSuitRPC(self):
        heart = common.HEART
        encoded = rpc.rpc_encode(heart)
        self.assertEqual(encoded, 3)
        decoded = rpc.rpc_decode(common.Suit, encoded)
        self.assertTrue(isinstance(decoded, common.Suit))
        self.assertEqual(heart.value, decoded.value)
        self.assertEqual(heart.name, decoded.name)

    def testCardRPC(self):
        card = Card(common.HEART, 5)
        encoded = rpc.rpc_encode(card)
        self.assertEqual(encoded, {'suit': 3, 'value': 5})
        self.assertFalse(isinstance(encoded, common.Card))
        decoded = rpc.rpc_decode(common.Card, encoded)
        self.assertTrue(isinstance(decoded, common.Card))
        self.assertEqual(card, decoded)

    def testCardSet(self):
        deck = CardSet.new_full_deck()
        self.assertTrue(len(deck) == 52)
        for suit in common.ALL_SUITS:
            cards = deck.get_cards(suit=common.HEART)
            self.assertTrue(len(cards) == 13)

        for i in range(2, 15):
            cards = deck.get_cards(value=i)
            self.assertTrue(len(cards) == 4)

        deck.clear()
        self.assertTrue(len(deck) == 0)

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
        self.assertTrue(hi is None)
        hi = cs.get_highest(floor=12)
        self.assertTrue(hi is None)

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
        self.assertTrue(lo is None)
        lo = cs.get_lowest(roof=2)
        self.assertTrue(lo is None)

    def testCardSetSort(self):
        cs = CardSet()
        cs.append(Card(common.HEART, 7))
        cs.append(Card(common.SPADE, 7))
        cs.append(Card(common.HEART, 5))
        cs.sort()
        sorted_cs = CardSet()
        sorted_cs.append(Card(common.SPADE, 7))
        sorted_cs.append(Card(common.HEART, 5))
        sorted_cs.append(Card(common.HEART, 7))
        self.assertEqual(cs, sorted_cs)

    def testGameStateRPC(self):
        gs = common.GameState()
        gs.table.append(Card(common.HEART, 5))
        encoded = rpc.rpc_encode(gs)
        gs2 = rpc.rpc_decode(common.GameState, encoded)
        self.assertTrue(isinstance(gs2, common.GameState))
        self.assertTrue(isinstance(gs2.table, gs.table.__class__))
        self.assertEqual(len(gs2.table), len(gs.table))
        self.assertEqual(gs2.table, gs.table)

    def testShortUUID(self):
        suuid = common.short_uuid()
        self.assertTrue(isinstance(suuid, str))
        suuid2 = common.short_uuid()
        self.assertNotEqual(suuid, suuid2)

    def testSynchronizedMethod(self):
        synctester = SyncTester()
        def _runner():
            synctester.sync()

        threads = []
        for i in range(4):
            thread = threading.Thread(None, _runner)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(5.0)

if __name__ == '__main__':
    unittest.main()
