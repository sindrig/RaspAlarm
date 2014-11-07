from raspalarm.conf import settings, getLogger

__all__ = ['notify_motion', 'notify_video']

logger = getLogger(__name__)

if settings.PUSHBULLET_API_KEY:
    from sender import notify_motion, notify_video
else:
    def log(*args, **kwargs):
        logger.debug('PUSHBULLET_API_KEY not defined')
    notify_motion = log
    notify_video = log
