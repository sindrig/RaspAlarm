import json
import os
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server

from raspalarm import get_camera_capturer, CaptureTypes

BASE_DIR = os.path.split(os.path.abspath(__file__))[0]
BLOCK_SIZE = 16 * 4096


class Portal(object):
    capturer = None

    def start_streaming(self, env):
        self.capturer = get_camera_capturer(CaptureTypes.STREAMER)()
        self.capturer.start_stream()
        return None, {'success': True}

    def get_stream_image(self, env):
        stream = self.capturer.get_image()
        headers = [('Content-Type', 'image/jpeg')]
        return headers, env['wsgi.file_wrapper'](stream, BLOCK_SIZE)

    def stop_streaming(self, env):
        if self.capturer:
            self.capturer.stop()
        return None, {'success': True}

p = Portal()


def application(environ, start_response):
    setup_testing_defaults(environ)

    function = environ.get('PATH_INFO', '').replace('/', '') or 'index.html'
    if os.path.exists(os.path.join(BASE_DIR, 'www', function)):
        status = '200 OK'
        headers = [('Content-type', get_content_type(function))]
        start_response(status, headers)
        f = open(os.path.join(BASE_DIR, 'www', function), 'r')
        return environ.get('wsgi.file_wrapper')(f, BLOCK_SIZE)
    elif not hasattr(p, function):
        status = '404 NOT FOUND'
        headers = [('Content-type', 'text/plain')]
        res = ''
    else:
        status = '200 OK'
        headers, res = getattr(p, function)(environ)

    if not headers:
        if isinstance(res, (str, unicode)):
            headers = [('Content-type', get_content_type(function))]
        else:
            headers = [('Content-type', 'application/json')]
            res = json.dumps(res)

    start_response(status, headers)

    if res:
        return res

    ret = ["%s: %s\n" % (key, value)
           for key, value in environ.iteritems()]
    return ret


def get_content_type(function):
    if function.endswith('.html'):
        return 'text/html'
    elif function.endswith('.js'):
        return 'text/javascript'
    return 'text/plain'


if __name__ == '__main__':
    PORT = 8080
    httpd = make_server('0.0.0.0', PORT, application)
    print 'Serving on port %s' % PORT
    httpd.serve_forever()
