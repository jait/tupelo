#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import unittest
import types
from tupelo import xmlrpc
from tupelo import rpc
from tupelo.xmlrpc import TupeloXMLRPCInterface as I
from tupelo.players import Player

class TestTupeloXMLRPCInterface(unittest.TestCase):

    def _encoded_player(self):
        player = Player('mörkö')
        encoded = rpc.rpc_encode(player)
        return encoded

    def testRegisterPlayer(self):
        iface = I()
        encoded = self._encoded_player()
        p_id = iface.register_player(encoded)
        self.assert_(isinstance(p_id, int))

    def testGame(self):
        iface = I()
        gamelist = iface.list_games()
        self.assert_(isinstance(gamelist, dict))
        self.assertEqual(len(gamelist), 0)
        # register
        p_encoded = self._encoded_player()
        p_id = iface.register_player(p_encoded)
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
        # after the only player leaves, the game should get deleted
        gamelist = iface.list_games()
        self.assertFalse(gamelist.has_key(g_id))


if __name__ == '__main__':
    unittest.main()
