#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sts=4 sw=4 et:

import unittest
from tupelo import rpc
from tupelo.server import TupeloRPCInterface as I, TupeloJSONDispatcher as D
from tupelo.players import Player

class TestTupeloJSONDispatcher(unittest.TestCase):

    def testPath2Method(self):
        d = D()
        self.assertEqual(d.json_path_prefix, '/api/') # default

        d.json_path_prefix = '/a/'
        self.assertEqual(d.path2method('/a/hello'), 'hello')
        self.assertEqual(d.path2method('/a/hello/again'), 'hello_again')
        self.assertEqual(d.path2method('/a/hello_again'), 'hello_again')
        self.assertEqual(d.path2method('/hello/again'), None)

        d.json_path_prefix = None
        self.assertEqual(d.path2method('/hello'), 'hello')
        self.assertEqual(d.path2method('hello'), 'hello')
        self.assertEqual(d.path2method('/hello/there'), 'hello_there')
        self.assertEqual(d.path2method('hello/again'), 'hello_again')

    def testParseQString(self):
        d = D()
        d.json_path_prefix = None
        f = d._json_parse_qstring
        self.assertEqual(f('/hello'), ('hello', {}))
        self.assertEqual(f('h?foo=bar'), ('h', {'foo': 'bar'}))
        self.assertEqual(f('h?foo="bar"'), ('h', {'foo': 'bar'}))
        self.assertEqual(f('h?a=1&b=3'), ('h', {'a': 1, 'b': 3}))
        self.assertEqual(f('h?a={"a":1, "b":[0], "c":"s"}'), ('h', {'a': {'a':1, 'b':[0], 'c': 's'}}))

    def testDispatch(self):
        class MockInterface(object):
            def __init__(self):
                self.callstack = []

            def _json_dispatch(self, method, params):
                self.callstack.append((method, params))

        mock = MockInterface()
        d = D()
        d.json_path_prefix = '/a/'
        d.register_instance(mock)
        d.json_dispatch('/a/hello', {})
        self.assertEqual(mock.callstack.pop(), ('hello', {}))
        d.json_dispatch('/a/h?a=1&b=2', {})
        self.assertEqual(mock.callstack.pop(), ('h', {'a':1, 'b':2}))
        d.json_dispatch('/a/h?a=1&b=2', {'Cookie': 'akey=b0_S6cNZRFmejfPXV2q6eA'})
        self.assertEqual(mock.callstack.pop(), ('h', {'a':1, 'b':2, 'akey': 'b0_S6cNZRFmejfPXV2q6eA'}))


class TestTupeloRPCInterface(unittest.TestCase):

    def _encoded_player(self, name='mörkö'):
        player = Player(name)
        encoded = rpc.rpc_encode(player)
        return encoded

    def testRegisterPlayer(self):
        iface = I()
        encoded = self._encoded_player()
        p_data = iface.player_register(encoded)
        self.assertTrue(isinstance(p_data['id'], str))
        self.assertTrue(isinstance(p_data['akey'], str))
        plr = iface._ensure_auth(p_data['akey'])
        self.assertEqual(plr.id, p_data['id'])
        # list players
        players_raw = iface.player_list(p_data['akey'])
        self.assertTrue(isinstance(players_raw, list))
        players = [rpc.rpc_decode(Player, pl) for pl in players_raw]
        me = None
        for pl in players:
            if pl.id == p_data['id']:
                me = pl
                break
        self.assertTrue(me is not None)
        self.assertEqual(me.player_name, encoded['player_name'])
        iface._clear_auth()

    def testHelloEmpty(self):
        iface = I()
        hello = iface.hello()
        self.assertTrue(isinstance(hello, dict))
        self.assertTrue('version' in hello)
        self.assertTrue(isinstance(hello['version'], str))
        self.assertFalse('player' in hello)
        self.assertFalse('game' in hello)

    def testGame(self):
        iface = I()
        gamelist = iface.game_list()
        self.assertTrue(isinstance(gamelist, dict))
        self.assertEqual(len(gamelist), 0)
        # register
        p_encoded = self._encoded_player()
        p_data = iface.player_register(p_encoded)
        # create game
        g_id = iface.game_create(p_data['akey'])
        # list
        gamelist = iface.game_list()
        self.assertTrue(str(g_id) in gamelist)
        players_raw = gamelist[str(g_id)]
        self.assertTrue(isinstance(players_raw, list))
        # decode
        players = [rpc.rpc_decode(Player, pl) for pl in players_raw]
        self.assertTrue(p_data['id'] in [pl.id for pl in players])
        # get_info
        info = iface.game_get_info(g_id)
        self.assertTrue(info == players_raw)
        # leave
        ret = iface.player_quit(p_data['akey'])
        self.assertEqual(ret, True)
        # after the only player leaves, the game should get deleted
        gamelist = iface.game_list()
        self.assertFalse(g_id in gamelist)

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
        self.assertTrue(str(g_id) in gamelist)
        players = gamelist[str(g_id)]
        self.assertEqual(len(players), len(p_datas))
        # decode
        players = [rpc.rpc_decode(Player, pl) for pl in players]
        for p_data in p_datas:
            self.assertTrue(p_data['id'] in [pl.id for pl in players])

        state = iface.game_get_state(p_datas[0]['akey'], g_id)
        self.assertTrue('game_state' in state)
        self.assertEqual(state['game_state']['status'], 0)

        try:
            ret = iface.game_start(p_datas[0]['akey'], g_id)
            self.assertEqual(ret, True)

            state = iface.game_get_state(p_datas[0]['akey'], g_id)
            self.assertTrue('game_state' in state)
            self.assertEqual(state['game_state']['status'], 1)
            self.assertTrue('hand' in state)

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
