import json
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server

from raspalarm import get_camera_capturer, CaptureTypes


class Portal(object):

    def start_streaming(self, env):
        self.streamer = get_camera_capturer(CaptureTypes.STREAMER)()
        self.streamer.start_stream()
        return None, {'success': True}

    def get_stream_image(self, env):
        lastid = 0
        stream = self.streamer.get_image(lastid)
        headers = [('Content-Type', 'image/jpeg')]
        return headers, stream

p = Portal()

def application(environ, start_response):
    setup_testing_defaults(environ)

    function = environ.get('PATH_INFO', '').replace('/', '')
    if not hasattr(p, function):
        status = '404 NOT FOUND'
        headers = [('Content-type', 'text/plain')]
        res = ''
    else:
        status = '200 OK'
        headers, res = getattr(p, function)(environ)

    if not headers:
        if isinstance(res, (str, unicode)):
            headers = [('Content-type', 'text/plain')]
        else:
            headers = [('Content-type', 'application/json')]
            res = json.dumps(res)

    start_response(status, headers)

    return res

    ret = ["%s: %s\n" % (key, value)
           for key, value in environ.iteritems()]
    return ret



if __name__ == '__main__':
    PORT = '8080'
    httpd = make_server('0.0.0.0', PORT, application)
    print 'Serving on port %s' % PORT
    httpd.serve_forever()
