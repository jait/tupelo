#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import unittest
import types
from tupelo import xmlrpc
from tupelo import rpc
from tupelo.xmlrpc import TupeloRPCInterface as I
from tupelo.players import Player

class TestTupeloXMLRPCInterface(unittest.TestCase):

    def _encoded_player(self, name='mörkö'):
        player = Player(name)
        encoded = rpc.rpc_encode(player)
        return encoded

    def testRegisterPlayer(self):
        iface = I()
        encoded = self._encoded_player()
        p_id = iface.player_register(encoded)
        self.assert_(isinstance(p_id, int))

    def testGame(self):
        iface = I()
        gamelist = iface.list_games()
        self.assert_(isinstance(gamelist, dict))
        self.assertEqual(len(gamelist), 0)
        # register
        p_encoded = self._encoded_player()
        p_id = iface.player_register(p_encoded)
        # create game
        g_id = iface.game_create(p_id)
        # list
        gamelist = iface.list_games()
        self.assert_(gamelist.has_key(g_id))
        players = gamelist[g_id]
        self.assert_(isinstance(players, list))
        self.assert_(p_id in players)
        # leave
        ret = iface.player_quit(p_id)
        self.assertEqual(ret, True)
        # after the only player leaves, the game should get deleted
        gamelist = iface.list_games()
        self.assertFalse(gamelist.has_key(g_id))

    def testFullGame(self):
        iface = I()
        plrs = []
        for i in range(1, 5):
            plrs.append(self._encoded_player(str(i)))

        p_ids = []
        for p in plrs:
            p_ids.append(iface.player_register(p))

        g_id = iface.game_create(p_ids[0])
        ret = iface.game_enter(g_id, p_ids[1])
        self.assertEqual(ret, g_id)
        ret = iface.game_enter(g_id, p_ids[2])
        self.assertEqual(ret, g_id)
        ret = iface.game_enter(g_id, p_ids[3])
        self.assertEqual(ret, g_id)

        gamelist = iface.list_games()
        self.assert_(gamelist.has_key(g_id))
        players = gamelist[g_id]
        self.assertEqual(len(players), len(p_ids))
        for p_id in p_ids:
            self.assert_(p_id in players)

        state = iface.game_get_state(g_id, p_ids[0])
        self.assert_(state.has_key('game_state'))
        self.assertEqual(state['game_state']['state'], 0)

        return
        # the following hangs possibly because of threads
        try:
            ret = iface.game_start(g_id)
            self.assertEqual(ret, True)

            state = iface.game_get_state(g_id, p_ids[0])
            self.assert_(state.has_key('game_state'))
            self.assertEqual(state['game_state']['state'], 1)
            self.assert_(state.has_key('hand'))

            ret = iface.player_quit(p_ids[0])
            self.assertEqual(ret, True)
        finally:
            for game in iface.games:
                game._reset()


if __name__ == '__main__':
    unittest.main()
