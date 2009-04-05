#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

from SimpleXMLRPCServer import SimpleXMLRPCServer
import xmlrpc

#PORT = 8052
PORT = xmlrpc.DEFAULT_PORT

def _runserver():
    """
    Run, Forrest! Run!
    """
    server = SimpleXMLRPCServer(('localhost', PORT))
    rpciface = xmlrpc.TupeloXMLRPCInterface()
    server.register_instance(rpciface)
    print 'Tupelo server serving at port %d' % PORT
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Shutting down'
        rpciface.game.shutdown()
        
if __name__ == '__main__':
    _runserver()
