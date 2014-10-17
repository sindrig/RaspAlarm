import traceback
import time
import io
from threading import Thread, Event
from Queue import Queue
import signal

import picamera
# from PIL import Image



class ImageRequest(object):
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
        print 'image taken in %0.2f seconds' % (time.time() - start)
        return req.stream

    def run(self):
        options = self._Thread__args[0]
        if not all(isinstance(x, int) or x.isdigit() for x in options.values()):
            raise TypeError('All options should be integers')
        with picamera.PiCamera() as camera:
            print 'self._running: %s' % self._running
            camera.start_preview()
            camera.resolution = (options['width'], options['height'])
            camera.brightness = options['brightness']
            camera.contrast = options['contrast']
            time.sleep(2)
            while self._running:
                if self.event.wait(1):
                    req = self.q.get()
                    print 'Starting capture...'
                    # time.sleep(0.5)
                    camera.capture(
                        req.stream,
                        format='jpeg',
                        # use_video_port=True,
                        thumbnail=None
                    )
                    print 'Image taken!'
                    req.notify()
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
            traceback.print_exc()

    def _start_stream(self, options):
        '''
            Starts our capturer
        '''
        self._streaming = 1
        self.capturer = Capturer(
            args=(options, )
        )
        self.capturer.start()
        def handler(signum, frame):
            print 'Killed with signum %s' % signum
            self.stop_stream()
            if signum == signal.SIGINT:
                raise KeyboardInterrupt()
            else:
                raise OSError('Unknown error')
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    def stop_stream(self):
        '''
            Stops our capturer
        '''
        self._streaming = 0
        self.capturer.terminate()
        self.capturer.join()

    stop = stop_stream

    def is_streaming(self):
        '''
            So we can know if a stream is currently running
        '''
        if self._streaming and not self.capturer._running:
            self._streaming = False
        return self._streaming

    def get_image(self):
        assert self._streaming, 'You have to call start_stream'
        return self.capturer.get_image()

if __name__ == '__main__':
    s = Streamer()
    s.start_stream()
    try:
        while s.is_streaming():
            print len(s.get_image().read())
            time.sleep(2)
    except Exception:
        import traceback; traceback.print_exc();
    finally:
        try:
            s.stop_stream()
        except Exception:
            import traceback; traceback.print_exc();
