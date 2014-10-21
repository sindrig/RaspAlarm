import os
import zipfile
import subprocess

from raspalarm.conf import settings, getLogger

logger = getLogger(__name__)

def pack_video(file_name):
    '''
        Packs the video so it is ready for distribution.
        Will use MP4Box and ZipFile if they are enabled in settings.
    '''
    logger.info('Packing video: %s', file_name)
    full_file_name = file_name
    loc, file_name = os.path.split(file_name)
    if settings.MOTION_VIDEO_ENABLE_MP4BOX:
        logger.debug('MP4Box enabled')
        new_file_name = get_file_name(loc, file_name, 'mp4')
        cmd = [
            settings.MP4BOX_EXECUTABLE,
            '-add',
            full_file_name,
            new_file_name
        ]
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        if proc.returncode:
            raise PackingError('\n'.join(proc.communicate()))
        logger.debug('Removing old file')
        os.remove(full_file_name)
        full_file_name = new_file_name

    if settings.MOTION_VIDEO_ENABLE_ZIP:
        logger.debug('ZipFile enabled')
        new_file_name = get_file_name(loc, file_name, 'zip')
        with zipfile.ZipFile(new_file_name, 'w') as z:
            z.write(full_file_name, arcname=os.path.split(full_file_name)[1])
        os.remove(full_file_name)
        logger.debug('Removing old file')

def get_file_name(loc, original_name, ext, preserve=0):
    '''
        Gets a new file name in loc with the same name as original_name
        and extension ext.
        If preserve is 0 (default) then we will try to delete the file
        with the same name as the one we are returning.
    '''
    nf = os.path.join(
        loc, os.path.splitext(original_name)[0] + '.' + ext
    )
    if not preserve:
        try:
            os.remove(nf)
        except OSError:
            pass
    return nf

class PackingError(IOError):
    pass

if __name__ == '__main__':
    import glob
    f = [
        k for k in glob.glob(
            os.path.join(
                settings.MOTION_VIDEO_DIR,
                '*.' + settings.MOTION_VIDEO_EXTENSION
            )
        )
    ][0]
    pack_video(f)
