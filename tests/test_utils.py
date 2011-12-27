#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import unittest
from tupelo import utils
import threading
import time

class SyncTester(object):

    def __init__(self):
        self.lock = threading.Lock()
        self.counter = 0

    @utils.synchronized_method('lock')
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

    def testShortUUID(self):
        suuid = utils.short_uuid()
        self.assert_(isinstance(suuid, basestring))
        suuid2 = utils.short_uuid()
        self.assertNotEqual(suuid, suuid2)

    def testSynchronizedMethod(self):
        synctester = SyncTester()
        def _runner():
            synctester.sync()

        threads = []
        for i in xrange(4):
            thread = threading.Thread(None, _runner)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(5.0)


if __name__ == '__main__':
    unittest.main()
