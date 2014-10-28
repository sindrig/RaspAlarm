import time

_RUNNING_CAPTURER = None

class CaptureTypes(object):
    STREAMER = 0
    MOTION = 1

def get_camera_capturer(_type, *args, **kwargs):
    global _RUNNING_CAPTURER
    from raspalarm.camera import motion, stream
    if _RUNNING_CAPTURER:
        _RUNNING_CAPTURER.stop()
        while _RUNNING_CAPTURER.is_alive():
            time.sleep(1)
    if _type == CaptureTypes.STREAMER:
        _RUNNING_CAPTURER = stream.Streamer(*args, **kwargs)
    elif _type == CaptureTypes.MOTION:
        _RUNNING_CAPTURER = motion.Detector(*args, **kwargs)
    else:
        raise NotImplementedError('Type %s not implemented yet' % _type)
    return _RUNNING_CAPTURER
