#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import unittest
import types
from tupelo import models

class TestObj(object):
    def __init__(self, foo=None, bar=None):
        self.foo = foo
        self.bar = bar

class TestModels(unittest.TestCase):

    def testManagerEmpty(self):
        m = models.Manager()
        self.assertEqual(m.get(), None)
        for obj in m.all():
            self.assert_(False)

    def testManager(self):
        m = models.Manager()
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
        m = models.Manager()
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
        m = models.Manager()
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
        m = models.Manager()
        o1 = TestObj(foo=1)
        o2 = TestObj(foo=1, bar=3)
        orig = [o1, o2]
        for obj in m:
            self.assert_(obj in orig)
            orig.remove(obj)

