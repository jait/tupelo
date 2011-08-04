#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import unittest
import time
from tupelo import players
from tupelo.common import GameState

class TestPlayers(unittest.TestCase):

    def testThreadedPlayer(self):
        plr = players.ThreadedPlayer('Seppo')
        plr.start()
        self.assert_(plr.isAlive())
        plr.game_state.state = GameState.STOPPED
        plr.act(None, None)
        plr.join(5.0) # wait until the thread quits
        self.assertFalse(plr.isAlive())

    def testThreadedPlayerStop(self):
        plr = players.ThreadedPlayer('Seppo')
        plr.start()
        time.sleep(1)
        self.assert_(plr.isAlive())
        plr.stop()
        plr.join(5.0) # wait until the thread quits
        self.assertFalse(plr.isAlive())

    def _testThreadedPlayerRestart(self):
        plr = players.ThreadedPlayer('Seppo')
        plr.start()
        time.sleep(1)
        self.assert_(plr.isAlive())
        plr.stop()
        plr.join(5.0) # wait until the thread quits
        self.assertFalse(plr.isAlive())
        # restart
        plr.start()
        self.assert_(plr.isAlive())
        plr.stop()
        plr.join(5.0) # wait until the thread quits
        self.assertFalse(plr.isAlive())


if __name__ == '__main__':
    unittest.main()
