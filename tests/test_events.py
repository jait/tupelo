#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import unittest
from tupelo import events
from tupelo import rpc
from tupelo import common
from tupelo import players

class TestEventsRPC(unittest.TestCase):

    def testEvent(self, cls=None):
        cls = events.Event
        e = cls()
        e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
        self.assertTrue(isinstance(e2, cls))
        self.assertEqual(e.type, e2.type)

    def testCardPlayedEmpty(self):
        cls = events.CardPlayedEvent
        e = cls()
        e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
        self.assertTrue(isinstance(e2, cls))
        self.assertEqual(e.type, e2.type)

    def testCardPlayed(self):
        cls = events.CardPlayedEvent
        plr = players.Player('Seppo')
        card = common.Card(common.HEART, 5)
        e = cls(plr, card)
        e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
        self.assertTrue(isinstance(e2, cls))
        self.assertEqual(e.type, e2.type)
        self.assertEqual(e.player.player_name, e2.player.player_name)
        self.assertEqual(e.card, e2.card)
        self.assertEqual(e2.game_state, None)

    def testMessageEmpty(self):
        cls = events.MessageEvent
        e = cls()
        e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
        self.assertTrue(isinstance(e2, cls))
        self.assertEqual(e.type, e2.type)

    def testMessage(self):
        e = events.MessageEvent('from', 'lorem ipsum')
        e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
        self.assertTrue(isinstance(e2, events.MessageEvent))
        self.assertEqual(e.type, e2.type)
        self.assertEqual(e.sender, e2.sender)
        self.assertEqual(e.message, e2.message)

    def testStateChanged(self):
        cls = events.StateChangedEvent
        game_state = common.GameState()
        game_state.state = common.GameState.VOTING
        e = cls(game_state)
        self.assertTrue(e.game_state is not None)
        e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
        self.assertTrue(isinstance(e2, cls))
        self.assertEqual(e.type, e2.type)
        self.assertEqual(e.game_state, e2.game_state)

    def testEventListEmpty(self):
        el = events.EventList()
        self.assertEqual(len(el), 0)
        el2 = rpc.rpc_decode(events.EventList, rpc.rpc_encode(el))
        self.assertTrue(isinstance(el2, events.EventList))
        self.assertEqual(len(el2), 0)

    def testEventList(self):
        el = events.EventList()
        el.append(events.MessageEvent('a', 'b'))
        el.append(events.MessageEvent('c', 'd'))
        num = len(el)
        self.assertEqual(num, 2)
        el2 = rpc.rpc_decode(events.EventList, rpc.rpc_encode(el))
        self.assertTrue(isinstance(el2, events.EventList))
        self.assertEqual(len(el2), num)
        for i in range(0, num):
            self.assertEqual(el[i], el2[i])


if __name__ == '__main__':
    unittest.main()
