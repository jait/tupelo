from typing import Optional
import json
import http.cookies
import urllib.parse
try:
    from urllib.parse import parse_qs
except:
    from cgi import parse_qs
from tupelo.common import ProtocolError


class TupeloJSONDispatcher():
    """
    Simple JSON dispatcher mixin that calls the methods of "instance" member.
    """

    json_path_prefix = '/api/'

    def __init__(self):
        self.instance = None

    def _json_parse_headers(self, headers) -> dict:
        """
        Parse the HTTP headers and extract any params from them.
        """
        params = {}
        # we support just 'akey' cookie
        cookie = http.cookies.SimpleCookie(headers.get('Cookie'))
        if 'akey' in cookie:
            params['akey'] = cookie['akey'].value

        return params

    def path2method(self, path: str) -> Optional[str]:
        """
        Convert a request path to a method name.
        """
        if self.json_path_prefix:
            if path.startswith(self.json_path_prefix):
                return path[len(self.json_path_prefix):].replace('/', '_')
            return None
        else:
            return path.lstrip('/').replace('/', '_')

    def _json_parse_qstring(self, qstring: str):
        """
        Parse a query string into method and parameters.

        Return a tuple of (method_name, params).
        """
        parsed = urllib.parse.urlparse(qstring)
        path = parsed[2]
        params = parse_qs(parsed[4])
        # use only the first value of any given parameter
        for k, v in list(params.items()):
            # try to decode a json parameter
            # if it fails, fall back to plain string
            try:
                params[k] = json.loads(v[0])
            except:
                params[k] = v[0]

        return (self.path2method(path), params)

    def register_instance(self, instance):
        """
        Register the target object instance.
        """
        self.instance = instance

    def json_dispatch(self, qstring: str, headers, body=None) -> str:
        """
        Dispatch a JSON method call to the interface instance.
        """
        method, qs_params = self._json_parse_qstring(qstring)
        if not method:
            raise ProtocolError('No such method')
        # alternatively, take params from body
        if not qs_params and body:
            (_, qs_params) = self._json_parse_qstring('?' + body.decode())

        # the querystring params override header params
        params = self._json_parse_headers(headers)
        params.update(qs_params)

        return json.dumps(self.instance._json_dispatch(method, params))
