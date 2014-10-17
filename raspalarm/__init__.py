from raspalarm.camera import motion, stream
_RUNNING_CAPTURER = None

class CaptureTypes(object):
    STREAMER = 0
    MOTION = 1

def get_camera_capturer(_type, *args, **kwargs):
    global _RUNNING_CAPTURER
    if _RUNNING_CAPTURER:
        _RUNNING_CAPTURER.stop()
    if _type == CaptureTypes.STREAMER:
        _RUNNING_CAPTURER = stream.Streamer(*args, **kwargs)
    elif _type == CaptureTypes.MOTION:
        _RUNNING_CAPTURER = motion.Detector(*args, **kwargs)
    else:
        raise NotImplementedError('Type %s not implemented yet' % _type)
    return _RUNNING_CAPTURER


def arm():
    pass

def disarm():
    pass
