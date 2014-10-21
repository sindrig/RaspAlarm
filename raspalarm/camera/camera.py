import os
import fcntl
import picamera
import picamera.array as array

from raspalarm.conf import settings


class ResourceError(IOError):
    pass

class Lock(object):

    def __init__(self, filename):
        self.filename = filename
        # This will create it if it does not exist already
        self.handle = open(filename, 'w')

    # Bitwise OR fcntl.LOCK_NB if you need a non-blocking lock
    def acquire(self):
        try:
            fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            raise ResourceError(
                'Only one camera instance can be used at the same time'
            )

    def release(self):
        fcntl.flock(self.handle, fcntl.LOCK_UN)

    def __del__(self):
        self.handle.close()

camlock = Lock(settings.LOCKFILE)


class PiCamera(picamera.PiCamera):
    _have_lock = False
    def __init__(self, *args, **kwargs):
        camlock.acquire()
        self._have_lock = True
        super(PiCamera, self).__init__(*args, **kwargs)
    def __enter__(self, *args, **kwargs):
        if not self._have_lock:
            camlock.acquire()
            self._have_lock = True
        return super(PiCamera, self).__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        camlock.release()
        self._have_lock = False
        return super(PiCamera, self).__exit__(*args, **kwargs)

# Exposing some other useful classes of picamera
PiCameraCircularIO = picamera.PiCameraCircularIO
PiVideoFrameType = picamera.PiVideoFrameType
