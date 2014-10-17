class LazySettings(object):
    PASSCODE = '1234'

    VIDEO_LENGTH = 10
    VIDEO_DIR = '/tmp/raspalarm/'
    VIDEO_RESOLUTION = (640, 480)

    def __getattr__(self, value):
        return None

settings = LazySettings()
