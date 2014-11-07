import datetime

from pushbullet import PushBullet

from raspalarm.conf import settings, getLogger
logger = getLogger(__name__)

pb = PushBullet(settings.PUSHBULLET_API_KEY)

def notify_video(video_file=None):
    logger.debug('Sending video %s', video_file)
    if video_file:
        pass
    else:
        notify_motion()

def notify_motion():
    logger.debug('Sending motion notify!')
    pb.push_note(
        'RaspAlarm: Motion detected!',
        'Motion detected at %s' % datetime.datetime.now().strftime(
            '%d.%m.%Y %H:%M:%S'
        )
    )
