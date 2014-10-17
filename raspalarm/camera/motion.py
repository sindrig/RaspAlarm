import traceback
import os
import datetime
import time
from Queue import Queue
from threading import Thread

import picamera
import picamera.array

from raspalarm.conf import settings


QUEUE_WAIT_TIME = 0.001


class VideoRequest(object):
    seconds = settings.VIDEO_LENGTH
    location = settings.VIDEO_DIR
    resolution = settings.VIDEO_RESOLUTION
    done = False

class Capturer(Thread):
    '''
        A thread that takes an image as soon as it's queue is empty.
        Has an open camera object all the time so we don't have to initialize
        it for every single image.
    '''
    _running = True

    def terminate(self):
        self._running = False

    def run(self):
        outq, inq, width, height = self._Thread__args
        with picamera.PiCamera() as camera:
            camera.resolution = (width, height)
            with picamera.array.PiRGBArray(camera) as stream:
                while self._running:
                    while not outq.empty():
                        print 'self.running: %s' % self._running
                        if not inq.empty():
                            req = inq.get()
                            if not os.path.exists(req.location):
                                os.makedirs(req.location)
                            camera.resolution = req.resolution
                            fn = 'motion_vid_%s.h264' % (
                                datetime.datetime.now().strftime(
                                    '%Y%m%d%H%M%S')
                            )
                            flocname = os.path.join(req.location, fn)
                            print 'saving to %s' % flocname
                            camera.start_recording(flocname)
                            camera.wait_recording(req.seconds)
                            camera.stop_recording()
                            print 'recording stopped!'
                            req.done = True
                            camera.resolution = (width, height)
                        if not self._running:
                            return
                        time.sleep(QUEUE_WAIT_TIME)
                    else:
                        camera.capture(stream, format='rgb')
                        outq.put(stream.array)
                        stream.truncate(0)


class Detector(object):
    width = 100
    height = 75
    picture_period = 0

    def __init__(self, threshold, sensitivity):
        self.threshold = threshold
        self.sensitivity = sensitivity
        self.lastImage = None
        self.outq = Queue()
        self.inq = Queue()
        self._detecting = 0

    def motion(self):
        '''
            Checks for diffs between the last image taken and a current one.
        '''
        ci = self.get_buffer()  # Current image
        li = self.lastImage  # Last image
        if not li is None:
            diff_count = 0L
            # Only compare the green channel (index number one)
            # since it has the highest quality.
            for diff in self._get_diff_values(ci, li, 1):
                if diff > self.threshold:
                    diff_count += 1
                if diff_count > self.sensitivity:
                    break
            else:
                self.lastImage = ci
                return False
            # Since the loop didn't exit cleanly we detected motion
            self.lastImage = ci
            return True
        else:
            self.lastImage = ci
            return False

    def _get_diff_values(self, im1, im2, channel):
        '''
            Get the difference between image 1 and image 2 on channel.
            Convert to int to prevent overflow, since
            our buffer values are saved as shorts.
        '''
        return (
            abs(int(im1[h][w][channel]) - int(im2[h][w][channel]))
            for w in xrange(0, self.width)
            for h in xrange(0, self.height)
        )

    def get_buffer(self):
        '''
            Gets an image buffer from our queue.
        '''
        while self.inq.empty():
            time.sleep(QUEUE_WAIT_TIME)
        return self.inq.get()

    def save_video(self):
        print 'saving video'
        req = VideoRequest()
        self.outq.put(req)
        while not req.done:
            # Wait until we have finished recording
            time.sleep(0.5)
        self.lastImage = None
        while not self.inq.empty():
            self.inq.get()
        return 0.5

    def start_detect(self, callback=save_video):
        '''
            Wrapper for _start_detect. Catches all exceptions and makes sure
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

    def _start_detect(self, callback):
        '''
            Starts taking pictures and comparing them for movement.
            Callback is called once motion is detected and is in charge
            of responding. If callback returns False we stop detecting.
            If callback returns a number we sleep for that amount
            of seconds.
        '''
        # TODO: Add threading
        self.start_detector()
        while self._detecting:
            if self.motion():
                print 'motion found!'
                # self.stop_detect()
                res = callback(self)
                if res:
                    if isinstance(res, (int, float)):
                        time.sleep(res)
                    else:
                        raise TypeError(
                            '%s returned type %d, expecting int or False'
                            %
                            (callback.__name__, res.__class__)
                        )
                else:
                    self.stop_detect()
                # self.start_detector()

    def start_detector(self):
        print 'starting detector'
        self._detecting = 1
        self.lastImage = None
        self.capturer = Capturer(
            args=(self.inq, self.outq, self.width, self.height)
        )
        self.capturer.start()

    def stop_detect(self):
        '''
            Stops detecting motion and kills our thread
        '''
        print 'stopping detector'
        # TODO: Add threading
        self.capturer.terminate()
        self._detecting = 0
        self.capturer.join()
        print 'capturer joined'

    stop = stop_detect

if __name__ == '__main__':
    detector = Detector(25, 25)
    detector = Detector(40, 200)

    def callback():
        print 'Detected motion @ %s!' % datetime.datetime.now().strftime(
            '%H:%M:%S')
        return 0.3
    # detector.start_detect(callback)
    detector.start_detect()
