import traceback
import os
import datetime
import time
import io
from operator import mul
from Queue import Queue
from threading import Thread
from PIL import Image, ImageChops

# import picamera.array
import numpy as np

from raspalarm.conf import settings, getLogger
import camera as picamera
import packer

logger = getLogger(__name__)
QUEUE_WAIT_TIME = 0.1


class VideoRequest(object):
    location = settings.MOTION_VIDEO_DIR
    done = False
    file_name = ''

class SettingsRequest(object):
    contrast = 0
    brightness = 50
    done = False

class Capturer(Thread):
    '''
        A thread that takes an image as soon as it's queue is empty.
        Has an open camera object all the time so we don't have to initialize
        it for every single image.
    '''
    _running = True
    _enable_stills = False  # Will be enabled later

    def terminate(self):
        self._running = False

    def run(self):
        try:
            self._run()
        except Exception:
            logger.error('Unknown error in motion.Capturer', exc_info=True)
            import traceback; traceback.print_exc();

    def _run(self):
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
            br = 5000000
            logger.debug('b:%d', camera.brightness)
            logger.debug('bitrate: %d', br)
            logger.debug('framerate %d', camera.framerate)
            videostream = picamera.PiCameraCircularIO(
                camera,
                seconds=settings.MOTION_VIDEO_LENGTH,
                bitrate=br
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
                            if isinstance(req, VideoRequest):

                                if not os.path.exists(req.location):
                                    os.makedirs(req.location)

                                logger.info(
                                    'Recording for %d seconds',
                                    settings.MOTION_VIDEO_LENGTH * 3 / 4
                                )
                                camera.wait_recording(
                                    settings.MOTION_VIDEO_LENGTH * 3 / 4
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
                                        # buf = videostream.read1()
                                        buf = videostream.read()
                                        if not buf:
                                            break
                                        output.write(buf)

                                # videostream.seek(0)
                                # videostream.truncate()
                                req.file_name = flocname
                                req.done = True
                            elif isinstance(req, SettingsRequest):
                                camera.brightness = req.brightness
                                camera.contrast = req.contrast
                                req.done = True
                            else:
                                logger.error('Received object %s in inq', req)

                        if outq.empty() and self._enable_stills:
                            stream = self.get_still(camera, width, height)
                            outq.put(stream.array)
                            stream.truncate()
                        camera.wait_recording(1)

                finally:
                    try:
                        camera.stop_recording()
                    except Exception:
                        pass

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
        time.sleep(1)


class Detector(Thread):
    width = 100
    height = 75
    picture_period = 0
    brightness_contrast_map = {
        10: -80,
        20: -60,
        30: -40,
        40: -20,
        50: 0,
        60: 20,
        70: 40,
        80: 60,
        90: 80,
        100: 100,
    }

    def __init__(self, threshold, sensitivity, callback=None, *args, **kwargs):
        self.threshold = threshold
        self.sensitivity = sensitivity
        self.lastImage = None
        self.outq = Queue()
        self.inq = Queue()
        self._detecting = 0
        self.callback = callback or self.save_video
        self.current_brightness = 50  # Initial value from picamera
        super(Detector, self).__init__(*args, **kwargs)

    def motion(self):
        '''
            Checks for diffs between the last image taken and a current one.
        '''
        ci = self.get_buffer()  # Current image
        if ci is None:
            # Possibly in case we get abruptly closed
            return False
        li = self.lastImage  # Last image
        cur_avg = self._get_average_value(ci)
        min_avg, max_avg = 85, 200
        if cur_avg < min_avg or cur_avg > max_avg and li is not None:
            brightness_adjustment = 10 if cur_avg < min_avg else -10
            if self.set_brightness(
                self.current_brightness + brightness_adjustment
            ):
                # Clear all images we have so we don't detect motion because
                # of our adjustments
                self.lastImage = None
                while self.get_buffer() is not None:
                    pass
                return False
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

    def set_brightness(self, new_value):
        if not new_value in self.brightness_contrast_map:
            return False
        logger.debug('Changing brightness from %d to %d',
                     self.current_brightness, new_value)
        req = SettingsRequest()
        req.brightness = new_value
        req.contrast = self.brightness_contrast_map[new_value] / 2
        self.outq.put(req)
        while not req.done and self.enabled():
            time.sleep(QUEUE_WAIT_TIME)
        self.current_brightness = new_value
        return True

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

    def _get_average_value(self, im):
        return np.average(im)

    def get_buffer(self):
        '''
            Gets an image buffer from our queue.
        '''
        if self.inq.empty():
            time.sleep(QUEUE_WAIT_TIME)
            return None
        return self.inq.get()

    def save_video(self):
        req = VideoRequest()
        self.outq.put(req)
        while not req.done and self.enabled():
            # Wait until we have finished recording
            time.sleep(0.5)
        self.lastImage = None
        try:
            packer.pack_video(req.file_name)
        except packer.PackingError:
            logger.error('Failed when trying to pack video!', exc_info=True)
        while not self.inq.empty():
            self.inq.get()
        logger.debug('save video finished (main)')
        return 0

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
                self.stop_detect()
            except Exception:
                logger.error('Could not terminate capturer!', exc_info=True)

    def run(self):
        try:
            self.start_detect()
        finally:
            try:
                if self.enabled():
                    self.stop_detect()
            except Exception:
                logger.error(
                    'Could not clean up, maybe we are okay though...',
                    exc_info=True
                )

    def _start_detect(self):
        '''
            Starts taking pictures and comparing them for movement.
            Callback is called once motion is detected and is in charge
            of responding. If callback returns False we stop detecting.
            If callback returns a number we sleep for that amount
            of seconds.
        '''
        self.start_capturer()
        while self._detecting:
            if not self.capturer.is_alive():
                return
            if self.motion():
                logger.debug('motion found!')
                res = self.callback()
                logger.debug('Callback returned %s', repr(res))
                if not res is None:
                    if isinstance(res, (int, float)):
                        if res:
                            time.sleep(res)
                    else:
                        raise TypeError(
                            '%s returned type %d, expecting int or False'
                            %
                            (self.callback.__name__, res.__class__)
                        )
                else:
                    logger.debug('callback returned None, so we stop')
                    self.stop_detect()

    def start_capturer(self):
        logger.debug('starting capturer')
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
        if self.capturer.is_alive():
            self.capturer.terminate()
            self.capturer.join(5)
        logger.debug('capturer joined')

    def enabled(self):
        '''
            Only returns true if our child thread is alive
        '''
        return self.capturer.is_alive()

    stop = stop_detect

if __name__ == '__main__':
    detector = Detector(25, 25)
    detector = Detector(40, 150)

    def callback():
        print 'Detected motion @ %s!' % datetime.datetime.now().strftime(
            '%H:%M:%S')
        return 0.3
    # detector.start_detect(callback)
    detector.start()
    try:
        while detector.is_alive():
            pass
    except KeyboardInterrupt:
        detector.stop()
