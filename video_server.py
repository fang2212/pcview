from flask import Flask, render_template, Response
from multiprocessing import Process, Manager
import cv2

app = Flask(__name__)

server_dict = Manager().dict()

server_dict['now_image'] = cv2.imread("./web/statics/jpg/160158-1541059318e139.jpg", cv2.IMREAD_COLOR)

def bgr2jpg(img):
    return cv2.imencode('.jpg', img)[1].tostring()


def get_image():
    while True:
        now_image = server_dict['now_image']
        frame = bgr2jpg(now_image)
        yield (b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('pcc.html')

@app.route('/video_feed')
def video_feed():
    return Response(get_image(), mimetype='multipart/x-mixed-replace; boundary=frame')


class VideoServer(Process):
    def __init__(self, port=1234):
        super().__init__()
        self.daemon = True
        self.port = port
    def run(self):
        app.run(host='0.0.0.0', port=self.port)
