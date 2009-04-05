#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpc import TupeloXMLRPCInterface

PORT = 8052

if __name__ == '__main__':
   
    server = SimpleXMLRPCServer(('localhost', PORT))
    rpciface = TupeloXMLRPCInterface()
    server.register_instance(rpciface)
    print 'Tupelo server serving at port %d' % PORT
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Shutting down'
        rpciface.game.shutdown()

