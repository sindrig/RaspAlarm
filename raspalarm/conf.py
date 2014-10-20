import logging
import logging.config


class LazySettings(object):
    PASSCODE = '1234'

    MOTION_VIDEO_LENGTH = 20
    MOTION_VIDEO_DIR = '/tmp/raspalarm/'
    MOTION_VIDEO_RESOLUTION = (640, 480)
    MOTION_VIDEO_PREFIX = 'motion'
    MOTION_VIDEO_EXTENSION = 'h264'

    TIME_BEFORE_ARM = 5

    MAIN_LOG_FILE = '/var/log/raspalarm.log'

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,  # this fixes the problem

        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level':'INFO',
                'class':'logging.handlers.RotatingFileHandler',
                'filename': MAIN_LOG_FILE,
                'maxBytes': 1024*1024*10,  # 10 MB
                'backupCount': 10,
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }

    def __getattr__(self, value):
        return None

settings = LazySettings()

def configure_logging():
    logging.config.dictConfig(settings.LOGGING)
