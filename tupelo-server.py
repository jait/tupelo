#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

from SimpleXMLRPCServer import SimpleXMLRPCServer
from optparse import OptionParser
import xmlrpc
import logging

def _runserver():
    """
    Run, Forrest! Run!
    """
    parser = OptionParser()
    parser.add_option("-p", "--port", dest='port', action="store",
            type="int", default=xmlrpc.DEFAULT_PORT,
            help="port number for the server")
    (opts, args) = parser.parse_args()
    format = "server: %(message)s"
    logging.basicConfig(level=logging.INFO, format=format)
    server = SimpleXMLRPCServer(('localhost', opts.port))
    rpciface = xmlrpc.TupeloXMLRPCInterface()
    server.register_instance(rpciface)
    logging.info('Tupelo server serving at port %d' % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Shutting down')
        rpciface.game.shutdown()
        
if __name__ == '__main__':
    _runserver()
