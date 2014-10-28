import signal
from threading import Thread as Original_Thread

from raspalarm.conf import settings, getLogger

logger = getLogger(__name__)


class Thread(Original_Thread):
    __registry = []

    @classmethod
    def destroy_all(cls, signum):
        for t in cls.__registry:
            if t.is_alive():
                t.stop()
                logger.debug(
                    'Killed "%s" with signum %s',
                    t.__class__.__name__,
                    signum
                )

    def start(self, *args, **kwargs):
        logger.debug('Starting thread %s', self.__class__.__name__)
        Thread.__registry.append(self)
        super(Thread, self).start(*args, **kwargs)


def handler(signum, frame):
    Thread.destroy_all(signum)
    if signum == signal.SIGINT:
        raise KeyboardInterrupt()
    else:
        raise OSError('Unknown error')
signal.signal(signal.SIGTERM, handler)
signal.signal(signal.SIGINT, handler)
