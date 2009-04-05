#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import xmlrpclib
import xmlrpc
import rpc

def _runclient():
    """
    Run, Forrest! Run!
    """
    server = xmlrpclib.ServerProxy('http://localhost:%d' % xmlrpc.DEFAULT_PORT)

    player = xmlrpc.XMLRPCCliPlayer('Humaani', server)
    player.id = server.register_player(rpc.rpc_encode(player))
    player.start()
    server.start_game_with_bots()
        
if __name__ == '__main__':
    _runclient()
