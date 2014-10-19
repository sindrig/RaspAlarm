import traceback
import os
import datetime
import time
import io
import logging
from Queue import Queue
from threading import Thread
from PIL import Image, ImageChops

import picamera
import picamera.array
import numpy as np

from raspalarm.conf import settings

logger = logging.getLogger(__name__)
QUEUE_WAIT_TIME = 0.1


class VideoRequest(object):
    location = settings.MOTION_VIDEO_DIR
    done = False

class Capturer(Thread):
    '''
        A thread that takes an image as soon as it's queue is empty.
        Has an open camera object all the time so we don't have to initialize
        it for every single image.
    '''
    _running = True
    _enable_stills = False  # Will be enabled

    def terminate(self):
        self._running = False

    def run(self):
        '''
            Records to a circularIO and relays stills from the video
            to the controller. Once the controller recognizes motion
            we continue recording video and notify the controller when
            we have finished.
            outq is the queue that we put stills to.
            inq is the queue we get video requests from. Getting a video
                request means that the controller detected motion
            width and height dictate the resolution to be used.
        '''
        outq, inq, width, height = self._Thread__args
        with picamera.PiCamera() as camera:
            camera.resolution = settings.MOTION_VIDEO_RESOLUTION
            videostream = picamera.PiCameraCircularIO(
                camera,
                seconds=settings.MOTION_VIDEO_LENGTH
            )
            with videostream:
                try:
                    camera.start_recording(
                        videostream,
                        format=settings.MOTION_VIDEO_EXTENSION
                    )
                    while self._running:
                        if not inq.empty():
                            req = inq.get()

                            if not os.path.exists(req.location):
                                os.makedirs(req.location)

                            logger.debug(
                                'Recording for %d seconds',
                                settings.MOTION_VIDEO_LENGTH / 2
                            )
                            camera.wait_recording(
                                settings.MOTION_VIDEO_LENGTH / 2
                            )

                            logger.debug('Stopped recording...')

                            fn = '%s_%s.%s' % (
                                settings.MOTION_VIDEO_PREFIX,
                                datetime.datetime.now().strftime(
                                    '%Y%m%d%H%M%S'),
                                settings.MOTION_VIDEO_EXTENSION
                            )
                            flocname = os.path.join(req.location, fn)

                            logger.debug('With (saving...)')
                            with io.open(flocname, 'wb') as output:
                                ft = picamera.PiVideoFrameType.sps_header
                                for frame in videostream.frames:
                                    if frame.frame_type == ft:
                                        videostream.seek(frame.position)
                                        break
                                while 1:
                                    buf = videostream.read1()
                                    if not buf:
                                        break
                                    output.write(buf)

                            videostream.seek(0)
                            videostream.truncate()
                            req.done = True
                        if outq.empty() and self._enable_stills:
                            stream = self.get_still(camera, width, height)
                            outq.put(stream.array)
                            stream.truncate()
                        camera.wait_recording(1)

                finally:
                    camera.stop_recording()

    def get_still(self, camera, width, height):
        imagestream = picamera.array.PiRGBArray(camera, size=(width, height))
        camera.capture(
            imagestream,
            format='rgb',
            use_video_port=True,
            resize=(width, height)
        )
        return imagestream

    def start_producting_stills(self):
        self._enable_stills = True


class Detector(Thread):
    width = 100
    height = 75
    picture_period = 0

    def __init__(self, threshold, sensitivity, callback=None, *args, **kwargs):
        self.threshold = threshold
        self.sensitivity = sensitivity
        self.lastImage = None
        self.outq = Queue()
        self.inq = Queue()
        self._detecting = 0
        self.callback = callback or self.save_video
        # self.width, self.height = settings.MOTION_VIDEO_RESOLUTION
        super(Detector, self).__init__(*args, **kwargs)

    def motion(self):
        '''
            Checks for diffs between the last image taken and a current one.
        '''
        ci = self.get_buffer()  # Current image
        li = self.lastImage  # Last image
        try:
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
                    return False
                # Since the loop didn't exit cleanly we detected motion
                return True
            else:
                return False
        finally:
            self.lastImage = ci

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
        logger.debug('saving video')
        req = VideoRequest()
        self.outq.put(req)
        while not req.done:
            # Wait until we have finished recording
            time.sleep(0.5)
        self.lastImage = None
        while not self.inq.empty():
            self.inq.get()
        logger.debug('save video finished (main)')
        return 0.5

    def start_detect(self):
        '''
            Wrapper for _start_detect. Catches all exceptions and makes sure
            we terminate our worker thread.
        '''
        try:
            self._start_detect()
        except KeyboardInterrupt:
            pass
        except Exception:
            logger.error('Could not start detection', exc_info=True)
        finally:
            try:
                self.capturer.terminate()
            except Exception:
                logger.error('Could not terminate capturer!', exc_info=True)

    run = start_detect

    def _start_detect(self):
        '''
            Starts taking pictures and comparing them for movement.
            Callback is called once motion is detected and is in charge
            of responding. If callback returns False we stop detecting.
            If callback returns a number we sleep for that amount
            of seconds.
        '''
        self.start_detector()
        while self._detecting:
            if self.motion():
                logger.debug('motion found!')
                # self.stop_detect()
                res = self.callback()
                if res:
                    if isinstance(res, (int, float)):
                        time.sleep(res)
                    else:
                        raise TypeError(
                            '%s returned type %d, expecting int or False'
                            %
                            (self.callback.__name__, res.__class__)
                        )
                else:
                    self.stop_detect()
                # self.start_detector()

    def start_detector(self):
        logger.debug('starting detector')
        self._detecting = 1
        self.lastImage = None
        self.capturer = Capturer(
            args=(self.inq, self.outq, self.width, self.height)
        )
        self.capturer.start()
        time.sleep(settings.TIME_BEFORE_ARM)
        self.capturer.start_producting_stills()

    def stop_detect(self):
        '''
            Stops detecting motion and kills our thread
        '''
        logger.debug('stopping detector')
        self._detecting = 0
        if self.capturer._running:
            self.capturer.terminate()
            self.capturer.join(5)
        logger.debug('capturer joined')

    stop = stop_detect

if __name__ == '__main__':
    detector = Detector(25, 25)
    detector = Detector(80, 200)

    def callback():
        print 'Detected motion @ %s!' % datetime.datetime.now().strftime(
            '%H:%M:%S')
        return 0.3
    # detector.start_detect(callback)
    detector.start()
    try:
        while 1:
            pass
    except KeyboardInterrupt:
        detector.stop()
