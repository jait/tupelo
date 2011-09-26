#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import unittest
import types
from tupelo import rpc
from tupelo.server import TupeloRPCInterface as I
from tupelo.players import Player

class TestTupeloRPCInterface(unittest.TestCase):

    def _encoded_player(self, name='mörkö'):
        player = Player(name)
        encoded = rpc.rpc_encode(player)
        return encoded

    def testRegisterPlayer(self):
        iface = I()
        encoded = self._encoded_player()
        p_data = iface.player_register(encoded)
        self.assert_(isinstance(p_data['id'], basestring))
        self.assert_(isinstance(p_data['akey'], basestring))
        plr = iface._ensure_auth(p_data['akey'])
        self.assertEqual(plr.id, p_data['id'])
        # list players
        players_raw = iface.player_list(p_data['akey'])
        self.assert_(isinstance(players_raw, list))
        players = [rpc.rpc_decode(Player, pl) for pl in players_raw]
        me = None
        for pl in players:
            if pl.id == p_data['id']:
                me = pl
                break
        self.assert_(me is not None)
        self.assertEqual(me.player_name, encoded['player_name'])
        iface._clear_auth()

    def testHelloEmpty(self):
        iface = I()
        hello = iface.hello()
        self.assert_(isinstance(hello, dict))
        self.assert_(hello.has_key('version'))
        self.assert_(isinstance(hello['version'], basestring))
        self.assertFalse(hello.has_key('player'))
        self.assertFalse(hello.has_key('game'))

    def testGame(self):
        iface = I()
        gamelist = iface.game_list()
        self.assert_(isinstance(gamelist, dict))
        self.assertEqual(len(gamelist), 0)
        # register
        p_encoded = self._encoded_player()
        p_data = iface.player_register(p_encoded)
        # create game
        g_id = iface.game_create(p_data['akey'])
        # list
        gamelist = iface.game_list()
        self.assert_(gamelist.has_key(str(g_id)))
        players_raw = gamelist[str(g_id)]
        self.assert_(isinstance(players_raw, list))
        # decode
        players = [rpc.rpc_decode(Player, pl) for pl in players_raw]
        self.assert_(p_data['id'] in [pl.id for pl in players])
        # get_info
        info = iface.game_get_info(g_id)
        self.assert_(info == players_raw)
        # leave
        ret = iface.player_quit(p_data['akey'])
        self.assertEqual(ret, True)
        # after the only player leaves, the game should get deleted
        gamelist = iface.game_list()
        self.assertFalse(gamelist.has_key(g_id))

    def testFullGame(self):
        iface = I()
        plrs = []
        for i in range(1, 5):
            plrs.append(self._encoded_player(str(i)))

        p_datas = []
        for p in plrs:
            p_datas.append(iface.player_register(p))

        g_id = iface.game_create(p_datas[0]['akey'])
        ret = iface.game_enter(p_datas[1]['akey'], g_id)
        self.assertEqual(ret, g_id)
        ret = iface.game_enter(p_datas[2]['akey'], g_id)
        self.assertEqual(ret, g_id)
        ret = iface.game_enter(p_datas[3]['akey'], g_id)
        self.assertEqual(ret, g_id)

        gamelist = iface.game_list()
        self.assert_(gamelist.has_key(str(g_id)))
        players = gamelist[str(g_id)]
        self.assertEqual(len(players), len(p_datas))
        # decode
        players = [rpc.rpc_decode(Player, pl) for pl in players]
        for p_data in p_datas:
            self.assert_(p_data['id'] in [pl.id for pl in players])

        state = iface.game_get_state(p_datas[0]['akey'], g_id)
        self.assert_(state.has_key('game_state'))
        self.assertEqual(state['game_state']['state'], 0)

        try:
            ret = iface.game_start(p_datas[0]['akey'], g_id)
            self.assertEqual(ret, True)

            state = iface.game_get_state(p_datas[0]['akey'], g_id)
            self.assert_(state.has_key('game_state'))
            self.assertEqual(state['game_state']['state'], 1)
            self.assert_(state.has_key('hand'))

            ret = iface.game_leave(p_datas[0]['akey'], g_id)
            self.assertEqual(ret, True)

            for p_data in p_datas:
                ret = iface.player_quit(p_data['akey'])
                self.assertEqual(ret, True)

        finally:
            for game in iface.games:
                game._reset()


if __name__ == '__main__':
    unittest.main()
