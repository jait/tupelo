#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import xmlrpclib
import xmlrpc
import rpc

if __name__ == '__main__':
   
    server = xmlrpclib.ServerProxy('http://localhost:%d' % xmlrpc.DEFAULT_PORT)

    pl = xmlrpc.XMLRPCCliPlayer('Humaani', server)
    pl.id = server.register_player(rpc.rpc_encode(pl))
    pl.start()
    server.start_game_with_bots()

