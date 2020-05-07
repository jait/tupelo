import logging
import json
from tupelo.server.jsonapi import TupeloJSONDispatcher
from tupelo.server import TupeloRPCInterface
from tupelo.common import GameError, RuleError, ProtocolError
from flask.wrappers import Request, Response
from werkzeug.datastructures import Headers

logger = logging.getLogger(__name__)

class Dispatcher(TupeloJSONDispatcher):

    json_path_prefix = '/'

    def __init__(self):
        super().__init__()
        self.instance = TupeloRPCInterface()

    def handle_request(self, request: Request):
        try:
            response = self.json_dispatch(request.full_path, request.headers, body=request.get_data())
        except ProtocolError as err:
            return Response(err.message, status=404)
        except (GameError, RuleError) as err:
            logger.exception(err)
            response = json.dumps({'code': err.rpc_code, 'message': str(err)})
            h = Headers()
            h.add('X-Error-Code', str(err.rpc_code))
            h.add('X-Error-Message', str(err))
            return Response(response, headers=h, status=403, content_type="application/json")
        except Exception as err:
            logger.exception(err)
            return Response(status=500)
        else:
            h = Headers()
            h.add("Cache-Control", "no-cache")
            h.add("Pragma", "no-cache")
            return Response(response, headers=h, status=200, content_type="application/json")

dispatcher = Dispatcher()

def handler(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """

    return dispatcher.handle_request(request)