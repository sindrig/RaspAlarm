#!/usr/bin/env python
import json
import os
import operator
import datetime
import glob
import urlparse
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
from StringIO import StringIO

from raspalarm.camera import get_camera_capturer, CaptureTypes
from raspalarm.conf import settings, getLogger

BASE_DIR = os.path.split(os.path.abspath(__file__))[0]
BLOCK_SIZE = 16 * 4096

logger = getLogger(__name__)


class Portal(object):
    capturer = None

    def start_streaming(self, env):
        if self.capturer and self.capturer.is_streaming():
            # Since we are already ready to start serving pictures,
            # we don't have to tell the client anything other than OK
            return None, {'success': True}
            # return None, {'success': False, 'error': 'Already streaming!'}
        self.capturer = get_camera_capturer(CaptureTypes.STREAMER)
        options = {}
        for k, v in self._parse_params(env['QUERY_STRING']).items():
            val = int(v[0]) if v[0].isdigit() else v[0]
            options[k.strip()] = val

        self.capturer.start_stream(options)
        return None, {'success': True}

    def get_stream_image(self, env):
        stream = self.capturer.get_image()
        headers = [('Content-Type', 'image/jpeg')]
        return headers, env['wsgi.file_wrapper'](stream, BLOCK_SIZE)

    def stop_streaming(self, env):
        if self.capturer:
            self.capturer.stop()
        return None, {'success': True}

    def download_videos(self, env):
        def extract_date_from_filename(fn):
            dtstr = fn.split('_')[-1].split('.')[0]
            return datetime.datetime.strptime(dtstr, '%Y%m%d%H%M%S')
        buf = StringIO()
        file_name_reg = '%s_%s.%s' % (
            settings.MOTION_VIDEO_PREFIX,
            '?' * 14,  # number of digits in timestamp
            settings.MOTION_VIDEO_FINAL_EXTENSION
        )
        file_names = glob.glob(
            os.path.join(
                settings.MOTION_VIDEO_DIR,
                file_name_reg
            )
        )
        files = []
        for fn in file_names:
            fn = os.path.split(fn)[-1]
            dt = extract_date_from_filename(fn)
            files.append((fn, dt))
        buf.write('<ul>')
        for fn, dt in sorted(files, key=operator.itemgetter(1)):
            buf.write(
                '<li><a href="/download_video/?v=%s">%s</a></li>' % (
                    fn,
                    dt.strftime('%a %-d. %b %Y at %H:%M:%S')
                )
            )
        buf.write('</ul>')
        buf.seek(0)
        headers = [('Content-type', 'text/html')]
        return headers, env.get('wsgi.file_wrapper')(buf, BLOCK_SIZE)

    def download_video(self, env):
        fn = self._parse_params(env['QUERY_STRING'])['v'][0]
        full_path = os.path.join(
            settings.MOTION_VIDEO_DIR,
            fn
        )
        if not os.path.isfile(full_path) or not full_path.endswith(
                settings.MOTION_VIDEO_FINAL_EXTENSION):
            res = '404'
        else:
            f = open(full_path, 'r')
            res = env.get('wsgi.file_wrapper')(f, BLOCK_SIZE)
        headers = [
            ('Content-type', 'video/H264'),
            ('content-Disposition', 'attachment; filename=%s' % fn)
        ]
        return headers, res



    def _parse_params(self, qs):
        return urlparse.parse_qs(qs)

p = Portal()


def application(environ, start_response):
    setup_testing_defaults(environ)

    function = environ.get('PATH_INFO', '').replace('/', '') or 'index.html'
    logger.info('Request for: %s', function)
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
        if res == '404':
            status = '404 NOT FOUND'
            res = ''

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
    logger.debug('Serving on port %s' % PORT)
    httpd.serve_forever()
