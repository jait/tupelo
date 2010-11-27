#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import unittest
import events
import rpc

class TestEventsRPC(unittest.TestCase):

   def testEvent(self, cls=None):
       cls = events.Event
       e = cls()
       e2 = rpc.rpc_decode(cls, rpc.rpc_encode(e))
       self.assert_(isinstance(e2, cls))
       self.assertEqual(e.type, e2.type)

   def testCardPlayedEmpty(self):
       cls = events.CardPlayedEvent
       e = cls()
       e2 = rpc.rpc_decode(cls, rpc.rpc_encode(e))
       self.assert_(isinstance(e2, cls))
       self.assertEqual(e.type, e2.type)

if __name__ == '__main__':
    unittest.main()
