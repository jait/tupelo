#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import unittest
import time
from tupelo import players
from tupelo.common import GameState

class TestPlayers(unittest.TestCase):

    def testThreadedPlayer(self, cls=None):
        plr = players.ThreadedPlayer('Seppo')
        plr.start()
        self.assert_(plr.isAlive())
        plr.game_state.state = GameState.STOPPED
        plr.act(None, None)
        time.sleep(2) # give the thread some time to quit itself
        self.assertFalse(plr.isAlive())
        plr.join()

    def testThreadedPlayerStop(self, cls=None):
        plr = players.ThreadedPlayer('Seppo')
        plr.start()
        self.assert_(plr.isAlive())
        plr.stop()
        time.sleep(2) # give the thread some time to quit itself
        self.assertFalse(plr.isAlive())
        plr.join()


if __name__ == '__main__':
    unittest.main()
