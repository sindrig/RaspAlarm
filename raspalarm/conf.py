class LazySettings(object):
    PASSCODE = '1234'

    MOTION_VIDEO_LENGTH = 20
    MOTION_VIDEO_DIR = '/tmp/raspalarm/'
    MOTION_VIDEO_RESOLUTION = (640, 480)
    MOTION_VIDEO_PREFIX = 'motion'
    MOTION_VIDEO_EXTENSION = 'h264'

    TIME_BEFORE_ARM = 5

    def __getattr__(self, value):
        return None

settings = LazySettings()
