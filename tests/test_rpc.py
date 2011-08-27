#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import unittest
from tupelo import rpc

class _RPCTestClass(rpc.RPCSerializable):
    rpc_attrs = ('a', 'b')
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

    def testDecodeAttr(self):
        testobj = _RPCTestClass()
        encoded = rpc.rpc_encode(testobj)
        self.assertEqual(encoded, {'a':1, 'b':'2'})
        decoded = _RPCTestClass()
        decoded.rpc_decode_attr(encoded, 'b')
        self.assertEqual(decoded.b, '2')

    def testSerializableEqual(self):
        testobj1 = _RPCTestClass()
        testobj2 = _RPCTestClass()
        self.assertEqual(testobj1, testobj2)
        self.assertFalse(testobj1 != testobj2)
        decoded1 = rpc.rpc_decode(_RPCTestClass, rpc.rpc_encode(testobj1))
        decoded2 = rpc.rpc_decode(_RPCTestClass, rpc.rpc_encode(testobj2))
        self.assertEqual(decoded1, decoded2)
        self.assertFalse(decoded1 != decoded2)

    def testSerializableEqualWrongType(self):
        testobj1 = _RPCTestClass()
        self.assertNotEqual(testobj1, [])
        self.assertTrue(testobj1 != [])
        self.assertNotEqual(testobj1, 'wrong type')
        self.assertNotEqual(testobj1, None)

    def testSerializableNotEqual(self):
        testobj1 = _RPCTestClass()
        testobj2 = _RPCTestClass()
        testobj2.a = 0
        self.assertNotEqual(testobj1, testobj2)
        self.assertFalse(testobj1 == testobj2)
        decoded1 = rpc.rpc_decode(_RPCTestClass, rpc.rpc_encode(testobj1))
        decoded2 = rpc.rpc_decode(_RPCTestClass, rpc.rpc_encode(testobj2))
        self.assertNotEqual(decoded1, decoded2)
        self.assertFalse(decoded1 == decoded2)

    def testSerializeCustom(self):
        testobj = _CustomClass()
        encoded = rpc.rpc_encode(testobj)
        self.assertEqual(encoded, 'hilipati')
        decoded = rpc.rpc_decode(_CustomClass, encoded)
        self.assertEqual(decoded, 'joop')


if __name__ == '__main__':
    unittest.main()
