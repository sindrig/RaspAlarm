import traceback
import time
import io
from threading import Event
from Queue import Queue
import signal

from raspalarm.conf import settings, getLogger
from raspalarm.modified_threading import Thread
import camera as picamera

logger = getLogger(__name__)


class ImageRequest(object):
    '''
        The controller will send an object of type ImageRequest and receive
        the image in it's buffer.
    '''
    def __init__(self):
        self.stream = io.BytesIO()
        self.finished = 0

    def notify(self):
        self.stream.seek(0)
        self.finished = 1

class Capturer(Thread):
    '''
        A thread that takes an image and returns it to a ImageRequest
        stream.
    '''
    _running = True

    def __init__(self, *args, **kwargs):
        self.event = Event()
        self.q = Queue()
        self.AUTO_SHUTDOWN_TIMER = settings.STREAM_AUTO_SHUTDOWN_TIMER
        super(Capturer, self).__init__(*args, **kwargs)

    def terminate(self):
        self._running = False

    stop = terminate

    def get_image(self):
        req = ImageRequest()
        self.q.put(req)
        self.event.set()
        start = time.time()
        while not req.finished and time.time() - start < 10:
            time.sleep(0.05)
        logger.info('image taken in %0.2f seconds', time.time() - start)
        return req.stream

    def run(self):
        options = self._Thread__args[0]
        STREAM_USE_CONTINOUS = settings.STREAM_USE_CONTINOUS
        if options.get('type', '') == 'basic':
            STREAM_USE_CONTINOUS = False
        with picamera.PiCamera() as camera:
            camera.start_preview()
            camera.resolution = (options['width'], options['height'])
            camera.brightness = options['brightness']
            camera.contrast = options['contrast']
            camera.vflip = settings.CAMERA_FLIP_VERTICAL
            camera.hflip = settings.CAMERA_FLIP_HORIZONTAL
            time.sleep(2)
            if settings.STREAM_USE_CONTINOUS:
                logger.debug('Using continuous stream')
                self.serve_forever_continuous(camera)
            else:
                logger.debug('Using basic stream')
                self.serve_forever_basic(camera)

    def serve_forever_continuous(self, camera):
        last_serve = time.time()
        stream = io.BytesIO()
        for img in camera.capture_continuous(stream, 'jpeg'):
            if not self._running:
                break
            stream.truncate()
            stream.seek(0)
            if self.event.is_set():
                req = self.q.get()
                while 1:
                    buf = stream.read()
                    if not buf:
                        break
                    req.stream.write(buf)
                req.notify()
                last_serve = time.time()
                self.event.clear()
            elif time.time() - last_serve > self.AUTO_SHUTDOWN_TIMER:
                logger.debug(
                    'Have not received request for image for %d seconds'
                    ', shutting down',
                    self.AUTO_SHUTDOWN_TIMER
                )
                self.terminate()
                # TODO: Maybe re-arm?

    def serve_forever_basic(self, camera):
            last_capture = time.time()
            while self._running:
                if time.time() - last_capture > self.AUTO_SHUTDOWN_TIMER:
                    logger.debug(
                        'Have not received request for image for %d seconds'
                        ', shutting down',
                        self.AUTO_SHUTDOWN_TIMER
                    )
                    self.terminate()
                    # TODO: Maybe re-arm?
                if not self.event.is_set():
                    # We have not yet received a request, so we take a picture
                    # and maybe when we are done we have received a request
                    last_pic = io.BytesIO()
                    camera.capture(last_pic, format='jpeg', thumbnail=None)
                    last_pic_time = time.time()
                else:
                    last_pic_time = None
                if self.event.wait(1):
                    req = self.q.get()
                    if last_pic_time and time.time() - last_pic_time < 0.5:
                        # If our last image is less then 0.5 seconds old, send
                        # that one to reduce wait time
                        req.stream = last_pic
                    else:
                        camera.capture(
                            req.stream,
                            format='jpeg',
                            # use_video_port=True,
                            thumbnail=None
                        )
                    req.notify()

                    last_capture = time.time()

                    if self.q.empty():
                        self.event.clear()


class Streamer(object):
    _streaming = 0
    options = {
        'width': 640,
        'height': 480,
        'brightness': 50,
        'contrast': 0
    }
    capturer = None

    def start_stream(self, options={}):
        '''
            Wrapper for _start_stream. Catches all exceptions and makes sure
            we terminate our worker thread.
        '''
        options = options or self.options
        if self.is_streaming():
            raise RuntimeError('Streamer is already streaming')
        try:
            self._start_stream(options)
        except KeyboardInterrupt:
            pass
        except Exception:
            logger.error('Could not start stream', exc_info=True)

    def _start_stream(self, options):
        '''
            Starts our capturer.
        '''
        self._streaming = 1
        self.capturer = Capturer(
            args=(options, )
        )
        self.capturer.start()

    def stop_stream(self):
        '''
            Stops our capturer.
        '''
        self._streaming = 0
        self.capturer.terminate()
        self.capturer.join()
        self.get_image = lambda slf: 0

    stop = stop_stream
    terminate = stop

    def is_streaming(self):
        '''
            So we can know if a stream is currently running.
        '''
        if self._streaming and not self.capturer.is_alive():
            self._streaming = False
        elif self.capturer and self.capturer.is_alive():
            self._streaming = True
        return self._streaming

    is_alive = is_streaming

    def get_image(self):
        '''
            Gets an image from our capturer object.
        '''
        if not self.is_streaming():
            self.start_stream()
        return self.capturer.get_image()

if __name__ == '__main__':
    s = Streamer()
    s.start_stream()
    try:
        while s.is_streaming():
            logger.info(str(len(s.get_image().read())))
            time.sleep(2)
    except Exception:
        logger.error('Unknown error', exc_info=True)
    finally:
        try:
            s.stop_stream()
        except Exception:
            logger.error('Could not stop stream', exc_info=True)
