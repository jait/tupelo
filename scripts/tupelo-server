#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

from optparse import OptionParser
from tupelo.server import DEFAULT_PORT, TupeloServer
import logging

LISTEN_ADDR = '' # or 'localhost'


def _runserver():
    """
    Run, Forrest! Run!
    """
    parser = OptionParser()
    parser.add_option("-p", "--port", dest='port', action="store",
            type="int", default=DEFAULT_PORT,
            help="port number for the server")
    (opts, args) = parser.parse_args()
    logformat = "server: %(message)s"
    logging.basicConfig(level=logging.INFO, format=logformat)
    tupelo_server = TupeloServer((LISTEN_ADDR, opts.port))
    logging.info('Tupelo server serving at port %d', opts.port)
    try:
        tupelo_server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Shutting down')
        tupelo_server.shutdown_games()

if __name__ == '__main__':
    _runserver()
