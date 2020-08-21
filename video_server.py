from flask import Flask, render_template, Response, session, jsonify, request, redirect, send_file, url_for
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
from multiprocessing import Process, Queue
import cv2
import time
import os
import shutil
from io import BytesIO
import zipfile
import json
import tarfile
# import for pyinstaller, do not delete
from engineio.async_drivers import eventlet
from eventlet.hubs import epolls, kqueue, selects
from dns import dnssec, e164, hash, namedict, tsigkeyring, update, version, zone
#

async_mode = 'eventlet'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# app.logger.setLevel('ERROR')
socketio = SocketIO(app, async_mode=async_mode)
# socketio.server.logger.setLevel(logging.ERROR)

# server_dict = Manager().dict()

# server_dict['now_image'] = cv2.imread("./web/statics/jpg/160158-1541059318e139.jpg", cv2.IMREAD_COLOR)

ctrl_q = Queue(maxsize=20)
msg_q = Queue(maxsize=200)
img_q = Queue(maxsize=5)
local_path = json.load(open('config/local.json'))['log_root']

no_frame = open('static/img/no_video.jpg', 'rb').read()

profile_data = {}

def make_targz(output_filename, source_dir):
    """
    一次性打包目录为tar.gz
    :param output_filename: 压缩文件名
    :param source_dir: 需要打包的目录
    :return: bool
    """
    try:
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

        return True
    except Exception as e:
        print(e)
        return False


def untar(fname, dest_dir):
    """
    解压tar.gz文件
    :param fname: 压缩文件名
    :param dest_dir: 解压后的存放路径
    :return: bool
    """
    try:
        t = tarfile.open(fname)
        t.extractall(path=dest_dir)
        return True
    except Exception as e:
        print(e)
        return False

def set_local_path(path):
    global local_path
    local_path = path

def push_profile_dt(src, dt):
    if src not in profile_data:
        profile_data[src] = {'up_since': time.time(), 'sum_t': 0, 'next_push': 0}

    profile_data[src]['sub_t'] += dt

    if time.time() > profile_data[src]['next_push']:
        msg_q.put(('misc', ))


def log2web(msg):
    if not isinstance(msg, str):
        return
    msg_q.put(('log', msg+'\n'))


def send_delay(name, delay):
    msg_q.put(('delay', {'name': name, 'delay': delay}))


def msg_send_task():
    while True:
        if not msg_q.empty():
            t0 = time.time()
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
            dt = time.time() - t0

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
        if os.path.exists(log):
            log_size = os.path.getsize(log)
        else:
            log_size = 0
        mtime = modify_time(path)
        recorded_data.append({'name': dir, 'path': path, 'log_size': sizeConvert(log_size), 'mtime': mtime})

    return recorded_data


def send_records():
    recorded_data = list_recorded_data(local_path)
    # print('recorded data:', recorded_data)
    socketio.emit('recorded', {'data': recorded_data, 'path': local_path}, namespace='/test')


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


def bgr2img(ftype, img):
    return cv2.imencode('.'+ftype, img)[1].tostring()

img_type = 'jpg'
def get_image():
    fscost = 0
    while True:
        try:
            if not img_q.empty():
                t0 = time.time()
                frame = bgr2img(img_type, img_q.get())
                socketio.sleep(0)
                dt = time.time() - t0
                fscost = fscost*0.9 +dt*0.1
                # log2web('frame send dt:{:.2f} q:{}'.format(dt*1000, img_q.qsize()))
                send_delay('frame_send_cost', '{:.1f}'.format(fscost*1000))
            else:
                # frame = no_frame
                socketio.sleep(0.01)
                continue
            yield b'--frame\r\n' + 'Content-Type: image/{}\r\n\r\n'.format(img_type).encode() + frame + b'\r\n'
            # socketio.sleep(0)
        except Exception as e:
            print(e)
            socketio.sleep(0.1)


@app.route('/')
def index():
    return render_template('cve_main.html', async_mode=socketio.async_mode)


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
    if cmd == 'rename':
        data = request.get_data(as_text=True)
        # print(data)
        log_path = os.path.join(local_path, item)
        if os.path.exists(log_path):
            # pass
            new_log_path = os.path.join(local_path, data)
            os.rename(log_path, new_log_path)
            print('renamed log', log_path, 'to', new_log_path)
    else:
        ctrl_q.put({'action': cmd, 'obj': item, 'initiator': 'web-local'})

    return redirect("/")


@app.route("/require/<item>", methods=['GET', 'POST'])
def require(item):
    # print('-----------------------------------------------------------------------', os.getpid())
    if item == 'records':
        send_records()

    return 'ok', 200


@app.route("/require/<dev_type>/<obj>/<item>", methods=['GET', 'POST'])
def require_type_item(dev_type, obj, item):
    # print('-----------------------------------------------------------------------', os.getpid())
    if dev_type == 'records':
        send_records()

    return 'ok', 200


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
    return send_file(memfile, attachment_filename='pcc_{}.zip'.format(item), as_attachment=True)


@app.route('/upgrade', methods=['POST', 'GET'])
def upgrade():
    if request.method == 'POST':
        f = request.files['file']
        # basepath = os.path.dirname(__file__)  # 当前文件所在路径
        upload_dir = '/home/minieye/upgrade_temp'
        upload_path = os.path.join(upload_dir, secure_filename(f.filename))
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
            os.mkdir(upload_dir)
        else:
            os.mkdir(upload_dir)
        f.save(upload_path)
        if upload_path.endswith('tar.gz'):
            dest_dir = os.path.join(upload_dir, 'unzip')
            os.mkdir(dest_dir)
            untar(upload_path, dest_dir)
            print('uploaded file depressed:', upload_path)
            if os.path.exists(os.path.join(dest_dir, 'pcc_app', 'pcc_app')):
                # shutil.copy(os.path.join(dest_dir, 'pcc_release', 'pcc'), 'pcc')
                # shutil.copy(os.path.join(dest_dir, 'pcc_release', 'build_info.txt'), 'build_info.txt')
                new_dir = os.path.join(dest_dir, 'pcc_app')
                for item in os.listdir('./'):
                    if os.path.isdir(item):
                        shutil.rmtree(item)
                    else:
                        continue
                        os.remove(item)
                for item in os.listdir(new_dir):
                    item_path = os.path.join(new_dir, item)
                    if os.path.isdir(item_path):
                        # continue
                        shutil.copytree(item_path, item)
                    else:
                        shutil.copy(item_path, item)
                print('replaced PCC executive, now restarting...')
                cmd_req = {'action': 'control', 'cmd': 'respawn'}
                ctrl_q.put(cmd_req)
        return redirect(url_for('upgrade'))
    return 'ok', 200


@socketio.on('connect', namespace='/test')
def test_connect():
    socketio.start_background_task(msg_send_task)
    # socketio.start_background_task(recorded_data_check_task)
    print('socketio client connected.')
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


class PccServer(Process):
    def __init__(self, port=1234):
        super().__init__()
        self.daemon = True
        self.port = port

    def run(self):
        # app.logger.setLevel(logging.ERROR)
        socketio.run(app, host='0.0.0.0', port=self.port)

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

    def close(self):
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()


if __name__ == "__main__":
    server = PccServer()
    server.start()
    cnt = 0
    while True:
        cnt += 1
        time.sleep(1)
        # print("running", cnt)
