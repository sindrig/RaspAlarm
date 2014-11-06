#!/usr/bin/env python
import json
import os
import operator
import datetime
import glob
import urlparse
import time
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
from StringIO import StringIO

from raspalarm.camera import get_camera_capturer, CaptureTypes
from raspalarm.conf import settings, getLogger
from raspalarm.keypad.monitor import Monitor
from raspalarm.temperature import reader, db, grapher

BASE_DIR = os.path.split(os.path.abspath(__file__))[0]
BLOCK_SIZE = 16 * 4096

logger = getLogger(__name__)


class Portal(object):
    capturer = None
    motion_detector = None

    def status(self, env):
        res = {}
        res['streaming'] = self.capturer and self.capturer.is_streaming()
        res['armed'] = self.motion_detector and self.motion_detector.is_alive()
        res['temp'] = '%0.2f' % reader.read()
        return None, res

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
        if self.capturer:
            stream = self.capturer.get_image()
            headers = [('Content-Type', 'image/jpeg')]
            return headers, env['wsgi.file_wrapper'](stream, BLOCK_SIZE)
        return None, '404'

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

    def arm_motion(self, env=None):
        self.capturer = None
        self.motion_detector = get_camera_capturer(CaptureTypes.MOTION)
        self.motion_detector.start()
        def keypad_fail():
            logger.error('WRONG PASSWORD SUPPLIED. TODO: NOTIFY?')
        Monitor.arm(self.disarm_motion, keypad_fail)
        return None, {'success': True}

    def disarm_motion(self, env=None):
        if self.motion_detector:
            self.motion_detector.stop()
            self._arm_monitor()
        return None, {'success': True}

    def view_temps(self, env):
        # Maybe TODO: Make this customizable?
        dt = datetime.datetime.now()
        fn = grapher.get_filename(dt)
        if not os.path.exists(fn):
            return None, '404'
        f = open(fn, 'r')
        headers = [('Content-Type', 'image/png')]
        return headers, env['wsgi.file_wrapper'](f, BLOCK_SIZE)
        timerange = (
            datetime.datetime.now() - datetime.timedelta(1),
            datetime.datetime.now()
        )
        connection = db.Database()
        data = connection.get_readings(timerange)
        logger.debug('Data received')
        json = {
            'data': [[timestamp * 1000, temp] for timestamp, temp in data],
        }
        return None, json
        img = grapher.create(x, y)
        headers = [('Content-Type', 'image/png')]
        return headers, env['wsgi.file_wrapper'](img, BLOCK_SIZE)

    def _arm_monitor(self):
        logger.debug('Arming monitor so we can arm with keypad')
        Monitor.arm(self.arm_motion, lambda: 0)

    def _parse_params(self, qs):
        return urlparse.parse_qs(qs)

p = Portal()


def application(environ, start_response):
    setup_testing_defaults(environ)

    function = environ.get('PATH_INFO', '').replace('/', '') or 'index.html'
    if function == 'index.html' and settings.SERVE_STATIC:
        function = 'index.local.html'
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


def serve_forever():
    p._arm_monitor()

    PORT = 8080
    httpd = make_server('0.0.0.0', PORT, application)
    logger.debug('Serving on port %s' % PORT)
    httpd.serve_forever()
