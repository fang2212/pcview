from flask import Flask, render_template, Response, stream_with_context, jsonify, request
from flask_socketio import SocketIO, emit
from multiprocessing import Process, Manager, Queue
import cv2
import time
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.logger.setLevel('ERROR')
socketio = SocketIO(app)
socketio.server.logger.setLevel(logging.ERROR)

server_dict = Manager().dict()

server_dict['now_image'] = cv2.imread("./web/statics/jpg/160158-1541059318e139.jpg", cv2.IMREAD_COLOR)

ctrl_q = Queue(maxsize=20)
msg_q = Queue(maxsize=200)


def msg_send_task():
    while True:
        if not msg_q.empty():
            data = msg_q.get()
            if not data:
                continue
            try:
                socketio.emit('misc', {'type': 'misc_data', 'data': data}, namespace='/test')
            except Exception as e:
                print(data)
                raise e
        else:
            socketio.sleep(0.01)


def ws_send(topic, msg, cb=None):
    if not topic or not msg:
        return
    try:
        socketio.emit(topic, msg, namespace='/test', callback=cb)
    except Exception as e:
        print(e)


def msg_send_task1():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(0.05)
        count += 1
        print('sockerio server sent msg 1')
        socketio.emit('misc',
                      {'type': 'log', 'data': {'type': 'lane', 'source': 'x1.2', 'info': 'Server generated event'},
                       'count': count}, namespace='/test')


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


@socketio.on('connect', namespace='/test')
def test_connect():
    socketio.start_background_task(msg_send_task)
    print('socketio client connected.')
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


class VideoServer(Process):
    def __init__(self, port=1234):
        super().__init__()
        self.daemon = True
        self.port = port
    def run(self):
        app.logger.setLevel(logging.ERROR)
        socketio.run(app, host='0.0.0.0', port=self.port, log_output='/dev/null')
