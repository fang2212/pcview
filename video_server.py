from flask import Flask, render_template, Response, stream_with_context, jsonify
from multiprocessing import Process, Manager, Queue
import cv2
import time

app = Flask(__name__)

server_dict = Manager().dict()

server_dict['now_image'] = cv2.imread("./web/statics/jpg/160158-1541059318e139.jpg", cv2.IMREAD_COLOR)

ctrl_q = Queue(maxsize=20)


def bgr2jpg(img):
    return cv2.imencode('.jpg', img)[1].tostring()

def bgr2bmp(img):
    return cv2.imencode('.bmp', img)[1].tostring()

def bgr2png(img):
    return cv2.imencode('.png', img)[1].tostring()


def get_image():
    while True:
        try:
            now_image = server_dict['now_image']
            # frame = bgr2jpg(now_image)
            # frame = bgr2bmp(now_image)
            frame = bgr2png(now_image)
            # yield (b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            # yield (b'--frame\r\n' + b'Content-Type: image/bmp\r\n\r\n' + frame + b'\r\n')
            yield (b'--frame\r\n' + b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(e)
            time.sleep(0.2)


@app.route('/')
def index():
    return render_template('cve_main.html')


@app.route('/video_feed')
def video_feed():
    return Response(get_image(), mimetype='multipart/x-mixed-replace; boundary=frame')
    # return Response(stream_with_context(get_image()))


@app.route("/control/<cmd>", methods=['GET', 'POST'])
def control(cmd):
    # message = "control"
    print('web control', cmd)
    if not ctrl_q.full():
        cmd_req = {'action': 'control', 'cmd': cmd, 'status': 'ok'}
        ctrl_q.put(cmd_req)
        return jsonify(cmd_req)


class VideoServer(Process):
    def __init__(self, port=1234):
        super().__init__()
        self.daemon = True
        self.port = port
    def run(self):
        app.run(host='0.0.0.0', port=self.port)
