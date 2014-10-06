from raspalarm import get_camera_capturer, CaptureTypes

from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
class Portal(object):

    def start_streaming(self):
        self.streamer = get_camera_capturer(CaptureTypes.STREAMER)()
        self.streamer.start_stream()

    def get_stream_image(self, lastid):
        stream = self.streamer.get_image(lastid)
        cherrypy.response.headers['Content-Type'] = 'image/jpeg'
        return file_generator(stream)

def application(environ, start_response):
    setup_testing_defaults(environ)

    status = '200 OK'
    headers = [('Content-type', 'text/plain')]

    start_response(status, headers)

    ret = ["%s: %s\n" % (key, value)
           for key, value in environ.iteritems()]
    return ret



if __name__ == '__main__':
    PORT = '8080'
    httpd = make_server('0.0.0.0', PORT, application)
    print 'Serving on port %s' % PORT
    httpd.serve_forever()
