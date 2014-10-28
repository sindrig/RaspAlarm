import logging
import logging.config


class LazySettings(object):

    BASE_DIR = '/mnt/ext/'

    PASSCODE = '1234'

    MOTION_THRESHOLD = 30
    MOTION_SENSITIVITY = 55
    MOTION_VIDEO_LENGTH = 20
    MOTION_VIDEO_DIR = BASE_DIR + 'videos/'
    MOTION_VIDEO_RESOLUTION = (720, 400)
    MOTION_VIDEO_PREFIX = 'motion'
    MOTION_VIDEO_EXTENSION = MOTION_VIDEO_FINAL_EXTENSION = 'h264'
    MOTION_VIDEO_ENABLE_MP4BOX = True
    MOTION_VIDEO_ENABLE_ZIP = False

    MP4BOX_EXECUTABLE = '/usr/bin/MP4Box'

    STREAM_AUTO_SHUTDOWN_TIMER = 60
    STREAM_USE_CONTINOUS = False

    TIME_BEFORE_ARM = 3

    MAIN_LOG_FILE = BASE_DIR + 'raspalarm.log'

    LOGLEVEL = 'DEBUG'

    LOCKFILE = '/var/lock/raspalarm.lock'

    DATABASE = BASE_DIR + 'db.sqlite3'

    TEMPERATURE_GRAPH_DIR = 'graphs/'

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
