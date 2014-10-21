import traceback
import time
import io
from threading import Thread, Event
from Queue import Queue
import signal

from raspalarm.conf import settings, getLogger
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
        if not all(isinstance(x, int) or x.isdigit() for x in options.values()):
            raise TypeError('All options should be integers')
        with picamera.PiCamera() as camera:
            camera.start_preview()
            camera.resolution = (options['width'], options['height'])
            camera.brightness = options['brightness']
            camera.contrast = options['contrast']
            time.sleep(2)
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
                    logger.info('Starting capture...')
                    # time.sleep(0.5)
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
                    logger.info('Image taken!')
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
        def handler(signum, frame):
            self.stop_stream()
            logger.debug('Killed with signum %s', signum)
            if signum == signal.SIGINT:
                raise KeyboardInterrupt()
            else:
                raise OSError('Unknown error')
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    def stop_stream(self):
        '''
            Stops our capturer.
        '''
        self._streaming = 0
        self.capturer.terminate()
        self.capturer.join()

    stop = stop_stream

    def is_streaming(self):
        '''
            So we can know if a stream is currently running.
        '''
        if self._streaming and not self.capturer._running:
            self._streaming = False
        return self._streaming

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
