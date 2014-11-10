import datetime

from pushbullet import PushBullet

from raspalarm.conf import settings, getLogger
logger = getLogger(__name__)

pb = PushBullet(settings.PUSHBULLET_API_KEY)

def notify_video(video_file=None):
    logger.debug('Sending video %s', video_file)
    if video_file:
        with open(video_file, 'rb') as f:
            success, file_data = pb.upload_file(
                f,
                datetime.datetime.now().strftime('%H:%M.mp4')
            )
        success, push = pb.push_file(**file_data)
        return success
    else:
        return notify_motion()

def notify_motion():
    logger.debug('Sending motion notify!')
    success, push = pb.push_note(
        'RaspAlarm: Motion detected!',
        'Motion detected at %s' % datetime.datetime.now().strftime(
            '%d.%m.%Y %H:%M:%S'
        )
    )
    return success

def notify_simple(text):
    logger.debug('Sending message: %s', text)
    success, push = pb.push_note(text, '')
    return success

if __name__ == '__main__':
    notify_video('/mnt/ext/videos/motion_20141028084726.mp4')
