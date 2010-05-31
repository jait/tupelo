#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import logging
import xmlrpc
from optparse import OptionParser
from players import CountingBotPlayer, DummyBotPlayer
from game import GameController

def _run_remote(server_addr):
    """
    Run, Forrest! Run!
    """
    if not server_addr.startswith('http://'):
        server_addr = 'http://' + server_addr

    game = xmlrpc.XMLRPCProxyController(server_addr)
    player = xmlrpc.XMLRPCCliPlayer('Humaani')
    game.register_player(player)
    player.start()
    game.start_game_with_bots()
    
def _run_local():
    """
    Run, Forrest! Run!
    """
    format = "%(message)s"
    logging.basicConfig(level=logging.DEBUG, format=format)
    game = GameController()

    #game.register_player(CliPlayer('Ihminen'))
    for i in range(0, 4):
        if i % 2 == 0:
            game.register_player(CountingBotPlayer('Lopotti %d' % i))
        else:
            game.register_player(DummyBotPlayer('Robotti %d' % i))

    game.start_game()
    game.wait_for_shutdown()
       
def _main():
    parser = OptionParser()
    parser.add_option("-r", "--remote", dest='remote', action="store_true",
            help="Play using a remote server")
    parser.add_option("-s", "--server", dest='server', action="store",
            type="string", metavar='SERVER:PORT', 
            default="localhost:%d" % xmlrpc.DEFAULT_PORT,
            help="Use given server and port")
    (opts, args) = parser.parse_args()

    if opts.remote:
        _run_remote(opts.server)
    else:
        _run_local()
        
if __name__ == '__main__':
    _main()
