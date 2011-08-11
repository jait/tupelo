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
        self.assert_(plr.is_alive())
        plr.game_state.state = GameState.STOPPED
        plr.act(None, None)
        plr.join(5.0) # wait until the thread quits
        self.assertFalse(plr.is_alive())

    def testThreadedPlayerStop(self):
        plr = players.ThreadedPlayer('Seppo')
        plr.start()
        time.sleep(0.5)
        self.assert_(plr.is_alive())
        plr.stop()
        plr.join(5.0) # wait until the thread quits
        self.assertFalse(plr.is_alive())

    def testThreadedPlayerRestart(self):
        plr = players.ThreadedPlayer('Seppo')
        plr.start()
        time.sleep(0.5)
        self.assert_(plr.is_alive())
        # trying to start again while running should raise an exception
        self.assertRaises(RuntimeError, plr.start)
        plr.stop()
        plr.join(5.0) # wait until the thread quits
        self.assertFalse(plr.is_alive())
        # restart
        plr.start()
        time.sleep(0.5)
        self.assert_(plr.is_alive())
        plr.stop()
        plr.join(5.0) # wait until the thread quits
        self.assertFalse(plr.is_alive())


if __name__ == '__main__':
    unittest.main()
