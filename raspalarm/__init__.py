from raspalarm.camera import motion, stream
_RUNNING_CAPTURER = None

class CaptureTypes(object):
    STREAMER = 0
    MOTION = 1

def get_camera_capturer(_type):
    if _RUNNING_CAPTURER:
        _RUNNING_CAPTURER.stop()
    if _type == CaptureTypes.STREAMER:
        return stream.Streamer
    elif _type == CaptureTypes.MOTION:
        return motion.Detector
    raise NotImplementedError('Type %s not implemented yet' % _type)
