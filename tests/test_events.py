#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import unittest
import events
import rpc

class TestEventsRPC(unittest.TestCase):

   def testEvent(self, cls=None):
       cls = events.Event
       e = cls()
       e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
       self.assert_(isinstance(e2, cls))
       self.assertEqual(e.type, e2.type)

   def testCardPlayedEmpty(self):
       cls = events.CardPlayedEvent
       e = cls()
       e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
       self.assert_(isinstance(e2, cls))
       self.assertEqual(e.type, e2.type)

   def testMessageEmpty(self):
       cls = events.MessageEvent
       e = cls()
       e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
       self.assert_(isinstance(e2, cls))
       self.assertEqual(e.type, e2.type)

   def testMessage(self):
       e = events.MessageEvent('from', 'lorem ipsum')
       e2 = rpc.rpc_decode(events.Event, rpc.rpc_encode(e))
       self.assert_(isinstance(e2, events.MessageEvent))
       self.assertEqual(e.type, e2.type)
       self.assertEqual(e.sender, e2.sender)
       self.assertEqual(e.message, e2.message)


if __name__ == '__main__':
    unittest.main()
