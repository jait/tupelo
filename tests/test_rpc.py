#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import unittest
import rpc

class _RPCTestClass(rpc.RPCSerializable):
    rpc_fields = ('a', 'b')
    a = 1
    b = '2'

class _CustomClass(object):
    def rpc_encode(self):
        return 'hilipati'

    @classmethod
    def rpc_decode(cls, rpcobj):
        return 'joop'

class TestRPC(unittest.TestCase):

   def testSerializeSimple(self):
       testobj = _RPCTestClass()
       encoded = rpc.rpc_encode(testobj)
       self.assertEqual(encoded, {'a':1, 'b':'2'})
       # change something
       encoded['a'] = 2
       decoded = rpc.rpc_decode(_RPCTestClass, encoded)
       self.assert_(isinstance(decoded, _RPCTestClass))
       self.assertEqual(decoded.a, 2)

   def testSerializeCustom(self):
       testobj = _CustomClass()
       encoded = rpc.rpc_encode(testobj)
       self.assertEqual(encoded, 'hilipati')
       decoded = rpc.rpc_decode(_CustomClass, encoded)
       self.assertEqual(decoded, 'joop')


if __name__ == '__main__':
    unittest.main()
