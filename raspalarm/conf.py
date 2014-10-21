import logging
import logging.config


class LazySettings(object):
    PASSCODE = '1234'

    MOTION_VIDEO_LENGTH = 20
    MOTION_VIDEO_DIR = '/tmp/raspalarm/'
    MOTION_VIDEO_RESOLUTION = (720, 400)
    # MOTION_VIDEO_RESOLUTION = (1080, 1000)
    MOTION_VIDEO_PREFIX = 'motion'
    MOTION_VIDEO_EXTENSION = MOTION_VIDEO_FINAL_EXTENSION = 'h264'
    MOTION_VIDEO_ENABLE_MP4BOX = True
    MP4BOX_EXECUTABLE = '/usr/bin/MP4Box'
    MOTION_VIDEO_ENABLE_ZIP = False

    STREAM_AUTO_SHUTDOWN_TIMER = 60

    TIME_BEFORE_ARM = 3

    MAIN_LOG_FILE = '/var/log/raspalarm.log'
    LOGLEVEL = 'DEBUG'

    LOCKFILE = '/var/lock/raspalarm.lock'

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,  # this fixes the problem

        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] '
                '%(threadName)s-%(name)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': LOGLEVEL,
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': MAIN_LOG_FILE,
                'maxBytes': 1024*1024*10,  # 10 MB
                'backupCount': 10,
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': LOGLEVEL,
                'propagate': True
            }
        }
    }

    def __init__(self):
        logging.config.dictConfig(self.LOGGING)

        if self.MOTION_VIDEO_ENABLE_ZIP:
            self.MOTION_VIDEO_FINAL_EXTENSION = 'zip'
        elif self.MOTION_VIDEO_ENABLE_MP4BOX:
            self.MOTION_VIDEO_FINAL_EXTENSION = 'mp4'


    def __getattr__(self, value):
        return None

settings = LazySettings()

getLogger = logging.getLogger
