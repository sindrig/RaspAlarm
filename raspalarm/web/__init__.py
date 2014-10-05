import cherrypy
from cherrypy.lib import file_generator
from raspalarm import get_camera_capturer, CaptureTypes


class Portal(object):

    @cherrypy.expose
    def start_streaming(self):
        self.streamer = get_camera_capturer(CaptureTypes.STREAMER)()
        self.streamer.start_stream()

    @cherrypy.expose
    def get_stream_image(self, lastid):
        stream = self.streamer.get_image(lastid)
        cherrypy.response.headers['Content-Type'] = 'image/jpeg'
        return file_generator(stream)


if __name__ == '__main__':
    cherrypy.quickstart(Portal())
