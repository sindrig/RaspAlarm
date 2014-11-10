from raspalarm.conf import settings, getLogger

__all__ = ['notify_motion', 'notify_video', 'notify_simple']

logger = getLogger(__name__)

if settings.PUSHBULLET_API_KEY:
    from sender import notify_motion, notify_video, notify_simple
else:
    def log(name):
        def do_log(*args, **kwargs):
            logger.debug('PUSHBULLET_API_KEY not defined, %s called', name)
        return do_log
    notify_motion = log('notify_motion')
    notify_video = log('notify_video')
    notify_simple = log('notify_simple')
