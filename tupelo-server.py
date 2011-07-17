#!/usr/bin/env python
# vim: set sts=4 sw=4 et:

import sys
import traceback
import SimpleXMLRPCServer
from optparse import OptionParser
from tupelo import xmlrpc
from tupelo.common import traced, ProtocolError
import logging
import json
import urlparse
try:
    from urlparse import parse_qs
except:
    from cgi import parse_qs


LISTEN_ADDR = '' # or 'localhost'

class TupeloRequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
    """
    Custom request handler class to support ajax/json RPC for GET requests and XML-RPC for POST.
    """

    @traced
    def do_GET(self):
        try:
            response = self.server.json_dispatch(self.path)
        except ProtocolError, err:
            self.report_404()
            return
        except Exception, err:
            traceback.print_exception(*sys.exc_info())
            self.send_response(500)
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

            # shut down the connection
            self.wfile.flush()
            self.connection.shutdown(1)


class TupeloServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
    """
    Custom server class that combines XML-RPC and JSON servers.
    """

    json_path_prefix = '/ajax/'

    def _json_parse_qstring(self, qstring):
        """
        Parse a query string into method and parameters.

        Return a tuple of (method_name, params).
        """
        parsed = urlparse.urlparse(qstring)
        path = parsed[2]
        params = parse_qs(parsed[4])
        # use only the first value of any given parameter
        for k, v in params.items():
            # try to decode a json parameter
            # if it fails, fall back to plain string
            try:
                params[k] = json.loads(v[0])
            except:
                params[k] = v[0]

        method = None
        if self.json_path_prefix:
            if path.startswith(self.json_path_prefix):
                method = path[len(self.json_path_prefix):].replace('/', '_')
        else:
            method = path.lstrip('/').replace('/', '_')

        return (method, params)

    def json_dispatch(self, qstring):
        """
        Dispatch a JSON method call to the interface instance.
        """
        method, params = self._json_parse_qstring(qstring)
        if not method:
            raise ProtocolError('No such method')

        return json.dumps(self.instance._json_dispatch(method, params))


def _runserver():
    """
    Run, Forrest! Run!
    """
    parser = OptionParser()
    parser.add_option("-p", "--port", dest='port', action="store",
            type="int", default=xmlrpc.DEFAULT_PORT,
            help="port number for the server")
    (opts, args) = parser.parse_args()
    logformat = "server: %(message)s"
    logging.basicConfig(level=logging.INFO, format=logformat)
    server = TupeloServer((LISTEN_ADDR, opts.port), TupeloRequestHandler)
    rpciface = xmlrpc.TupeloRPCInterface()
    server.register_instance(rpciface)
    logging.info('Tupelo server serving at port %d', opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Shutting down')
        for game in rpciface.games:
            game.shutdown()
        
if __name__ == '__main__':
    _runserver()
