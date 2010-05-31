#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

from SimpleXMLRPCServer import SimpleXMLRPCServer
import xmlrpc
import logging

#PORT = 8052
PORT = xmlrpc.DEFAULT_PORT

def _runserver():
    """
    Run, Forrest! Run!
    """
    format = "server: %(message)s"
    logging.basicConfig(level=logging.INFO, format=format)
    server = SimpleXMLRPCServer(('localhost', PORT))
    rpciface = xmlrpc.TupeloXMLRPCInterface()
    server.register_instance(rpciface)
    logging.info('Tupelo server serving at port %d' % PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Shutting down')
        rpciface.game.shutdown()
        
if __name__ == '__main__':
    _runserver()
