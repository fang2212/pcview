from flask import Flask, render_template, Response, stream_with_context, jsonify, request, redirect, send_file
from flask_socketio import SocketIO, emit
from multiprocessing import Process, Manager, Queue
import cv2
import time
import os
import logging
from io import BytesIO
import zipfile
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.logger.setLevel('ERROR')
socketio = SocketIO(app)
socketio.server.logger.setLevel(logging.ERROR)

server_dict = Manager().dict()

server_dict['now_image'] = cv2.imread("./web/statics/jpg/160158-1541059318e139.jpg", cv2.IMREAD_COLOR)

ctrl_q = Queue(maxsize=20)
msg_q = Queue(maxsize=200)
local_path = json.load(open('config/local.json'))['log_root']


def msg_send_task():
    while True:
        if not msg_q.empty():
            data = msg_q.get()
            if not data:
                continue
            try:
                topic, msg = data
                # print(topic, data)
                socketio.emit(topic, {'data': msg}, namespace='/test')
            except Exception as e:
                print(data)
                raise e
        else:
            socketio.sleep(0.01)


def list_recorded_data(log_path='/home/nan/data/pcc'):
    def sizeConvert(size):  # 单位换算
        K, M, G = 1024, 1024 ** 2, 1024 ** 3
        if size >= G:
            return '{:.2f} GiB'.format(size / G)
        elif size >= M:
            return '{:.2f} MiB'.format(size / M)
        elif size >= K:
            return '{:.2f} KiB'.format(size / K)
        else:
            return '{:.2f} Bytes'.format(size)

    def modify_time(file_path):
        mtime = os.stat(file_path).st_mtime
        file_modify_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        return file_modify_time
    dirs = sorted(os.listdir(log_path), reverse=True)
    recorded_data = list()
    for dir in dirs:
        path = os.path.join(log_path, dir)
        log = os.path.join(log_path, dir, 'log.txt')
        log_size = os.path.getsize(log)
        mtime = modify_time(path)
        recorded_data.append({'name': dir, 'path': path, 'log_size': sizeConvert(log_size), 'mtime': mtime})

    return recorded_data


def recorded_data_check_task(log_path=local_path):
    while True:
        recorded_data = list_recorded_data(log_path)
        print('recorded data:', recorded_data)
        socketio.emit('recorded', {'data': recorded_data, 'path': log_path}, namespace='/test')
        socketio.sleep(5)


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
            # if not now_image:
                # time.sleep(0.2)
                # continue
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
    return render_template('cve_main_bootstrap.html')


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


@app.route("/action/<cmd>/<item>", methods=['GET', 'POST'])
def control_obj(cmd, item):
    if cmd == 'replay':
        print('replay on web.')
    elif cmd == 'analyze':
        print('analyze on web.')

    return redirect("/")


@app.route("/require/<item>", methods=['GET', 'POST'])
def require(item):
    if item == 'records':
        recorded_data = list_recorded_data(local_path)
        print('recorded data:', recorded_data)
        socketio.emit('recorded', {'data': recorded_data, 'path': local_path}, namespace='/test')

    return 200


@app.route("/download/<item>", methods=['GET', 'POST'])
def download(item):
    print('downloading', item)
    dir_path = os.path.join(local_path, item)
    if not os.path.exists(dir_path):
        return jsonify({'status': 'not found'})
    memfile = BytesIO()
    with zipfile.ZipFile(memfile, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path, dirnames, filenames in os.walk(dir_path):
            # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
            fpath = path.replace(dir_path, '')
            fpath = fpath and fpath + os.sep or ''
            for filename in filenames:
                zf.write(os.path.join(path, filename), os.path.join(fpath, filename))
    memfile.seek(0)
    return send_file(memfile, attachment_filename='pcc_{}'.format(item), as_attachment=True)


@socketio.on('connect', namespace='/test')
def test_connect():
    socketio.start_background_task(msg_send_task)
    # socketio.start_background_task(recorded_data_check_task)
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

    def ws_send(self, topic, msg, cb=None):
        if not topic or not msg:
            return
        try:
            socketio.emit(topic, msg, namespace='/test', callback=cb)
        except Exception as e:
            print(e)

    def run_background(self, task):
        socketio.start_background_task(task)
        print('background task started:', task.__name__)

