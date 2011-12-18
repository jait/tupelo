#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import unittest
from tupelo import dal

class TestObj(object):
    def __init__(self, foo=None, bar=None):
        self.foo = foo
        self.bar = bar

class TestModels(unittest.TestCase):

    def testManagerEmpty(self):
        m = dal.Manager()
        self.assertEqual(m.get(), None)
        for obj in m.all():
            self.assert_(False)

    def testManager(self):
        m = dal.Manager()
        res = m.all()
        self.assertEqual(len(res), 0)
        o1 = TestObj(foo=1)
        o2 = TestObj(foo=2, bar=3)
        m.append(o1)
        m.append(o2)
        self.assertEqual(m.get(foo=1), o1)
        self.assertEqual(m.get(foo=2, bar=3), o2)
        res = m.all()
        self.assertEqual(len(res), 2)
        self.assert_(o1 in res)
        self.assert_(o2 in res)

    def testManagerRemove(self):
        m = dal.Manager()
        o1 = TestObj(foo=1)
        o2 = TestObj(foo=2, bar=3)
        m.append(o1)
        m.append(o2)
        m.remove(o1)
        self.assertEqual(len(m.objects), 1)
        self.assertEqual(m.get(), o2)
        m.remove(m.get())
        self.assertEqual(len(m.objects), 0)

    def testManagerFilter(self):
        m = dal.Manager()
        o1 = TestObj(foo=1)
        o2 = TestObj(foo=1, bar=3)
        m.append(o1)
        m.append(o2)
        res = m.filter(foo=1)
        self.assertEqual(len(res), 2)
        self.assert_(o1 in res)
        self.assert_(o2 in res)
        res = m.filter(bar=3)
        self.assertEqual(len(res), 1)
        self.assert_(o2 in res)
        res = m.filter(notthere=1)
        self.assertEqual(len(res), 0)

    def testManagerIter(self):
        m = dal.Manager()
        o1 = TestObj(foo=1)
        o2 = TestObj(foo=1, bar=3)
        orig = [o1, o2]
        for obj in m:
            self.assert_(obj in orig)
            orig.remove(obj)


class TestFields(unittest.TestCase):

    def testBaseField(self):
        class Doc(dal.Document):
            f1 = dal.BaseField()
            f2 = dal.BaseField()
            f3 = dal.BaseField(allow_none=False)

        foo1 = Doc()
        foo2 = Doc()
        self.assertEqual(foo1.f1, None)

        foo1.f1 = 41 
        foo1.f2 = 42 
        self.assertEqual(foo1.f1, 41)
        self.assert_(isinstance(foo1.f1, int))
        self.assertEqual(foo1.f2, 42)
        self.assertEqual(foo2.f1, None)

        foo2.f1 = 'something different' 
        self.assertEqual(foo2.f1, 'something different')
        self.assert_(isinstance(foo2.f1, basestring))

        foo1.f1 = None
        self.assertEqual(foo1.f1, None)
        self.assert_(isinstance(Doc.f1, dal.BaseField))

        foo1.f3 = 0
        self.assertEqual(foo1.f3, 0)
        self.assertRaises(TypeError, setattr, foo1, 'f3', None)

    def testStringField(self):
        class Doc(dal.Document):
            s = dal.StringField()

        doc = Doc()
        self.assertEqual(doc.s, None)
        doc.s = 'hilipati'
        self.assertEqual(doc.s, 'hilipati')
        self.assertRaises(TypeError, setattr, doc, 's', 1)
        self.assertRaises(TypeError, setattr, doc, 's', ['string'])
        self.assertEqual(doc.s, 'hilipati')
        doc.s = None
        self.assertEqual(doc.s, None)

    def testIntegerField(self):
        class Doc(dal.Document):
            i = dal.IntegerField()

        doc = Doc()
        self.assertEqual(doc.i, None)
        doc.i = 42
        self.assertEqual(doc.i, 42)
        self.assertRaises(TypeError, setattr, doc, 'i', 'string')
        self.assertRaises(TypeError, setattr, doc, 'i', [0])
        self.assertRaises(TypeError, setattr, doc, 'i', 0.0)
        self.assertEqual(doc.i, 42)
        doc.i = None
        self.assertEqual(doc.i, None)
