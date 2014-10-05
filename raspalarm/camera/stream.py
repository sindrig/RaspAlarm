import traceback
import time
import io
from threading import Thread

import picamera
# from PIL import Image


IMAGE_REFRESH_TIME = 1

NEWEST_IMAGE = None


class Capturer(Thread):
    '''
        A thread that takes an image and stores it in a global variable
        every IMAGE_REFRESH_TIME seconds.
    '''
    _running = True

    def terminate(self):
        self._running = False

    def run(self):
        width, height = self._Thread__args
        with picamera.PiCamera() as camera:
            while self._running:
                camera.resolution = (width, height)
                stream = io.BytesIO()
                camera.capture(stream, format='jpeg')
                stream.seek(0)
                # NEWEST_IMAGE = (time.time(), Image.open(stream))
                NEWEST_IMAGE = (time.time(), stream.read())
                time.sleep(IMAGE_REFRESH_TIME)


class Streamer(object):
    width = 800
    height = 600
    _streaming = 0

    def start_stream(self):
        '''
            Wrapper for _start_stream. Catches all exceptions and makes sure
            we terminate our worker thread.
        '''
        try:
            self._start_detect(callback)
        except KeyboardInterrupt:
            pass
        except Exception:
            traceback.print_exc()
        finally:
            try:
                self.capturer.terminate()
            except Exception:
                traceback.print_exc()

    def _start_stream(self, callback):
        '''
            Starts our capturer
        '''
        self._streaming = 1
        self.capturer = Capturer(
            args=(self.width, self.height)
        )
        self.capturer.start()

    def stop_stream(self):
        '''
            Stops our capturer
        '''
        self._streaming = 0
        self.capturer.terminate()
        self.capturer.join()

    stop = stop_stream

    def get_image(self, lasttime):
        assert self._streaming, 'You have to call start_stream'
        while not NEWEST_IMAGE or lasttime == NEWEST_IMAGE[0]:
            time.sleep(IMAGE_REFRESH_TIME / 10.0)
        return NEWEST_IMAGE[1]

if __name__ == '__main__':
    pass
