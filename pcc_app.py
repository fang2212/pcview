import sys
import os
local_path = os.path.split(os.path.realpath(__file__))[0]
os.chdir(local_path)

from config.config import dic2obj, bcl, load_cfg
import argparse
import json
import cv2
from pcc import *
from tools.mytools import Supervisor
import shutil
import platform
from sink.hub import Hub
from threading import Thread

machine_arch = platform.machine()


cfgfile = 'config/cfg_lab.json'

parser = argparse.ArgumentParser(description="process CVE log.")
parser.add_argument('cfg_path', nargs='?', default=cfgfile)
parser.add_argument('-o', '--output', default=None)
parser.add_argument('-d', '--direct', default=None)
parser.add_argument('-c', '--config', default=None)
parser.add_argument('-hl', '--headless', help='headless mode', action="store_true")
parser.add_argument('-a', '--auto', help='auto recording', action="store_true")
parser.add_argument('-w', '--web', help='web ui', action="store_true")
# load_cfg(sys.argv[1])

args = parser.parse_args()
mount_root = '/mnt/'
# if len(sys.argv) == 1:
#     sys.argv.append(cfgfile)
local_cfg = dic2obj(json.load(open('config/local.json')))
# if machine_arch != 'x86_64':
try:
    udevs = os.listdir(mount_root)
    if not udevs:
        raise FileNotFoundError
    dir_found = False
    for udev in udevs:
        lpath = os.path.join(mount_root, udev, 'cve_data')
        if os.path.exists(lpath):
            print('found cve dir', lpath)
            local_cfg.log_root = lpath
            dir_found = True
            break
    if not dir_found:
        lpath = os.path.join(mount_root, udevs[0], 'cve_data')
        print('creating cve dir')
        os.mkdir(lpath)
        local_cfg.log_root = lpath
except FileNotFoundError:
    print('no media folder found. using home dir as default.')
# else:
#     print('x86_64 architect found, using high profile.')
# opath = args.output or local_cfg.log_root
# local_cfg.log_root = opath
if args.output:
    local_cfg.log_root = args.output

if args.config:
    cve_conf = load_cfg(args.config)
else:
    cve_conf = load_cfg(args.cfg_path)
cve_conf.local_cfg = local_cfg
print(cve_conf.local_cfg.log_root)

_startup_cwd = os.getcwd()


def respawn(self=None):
    """Re-execute the current process.

    This must be called from the main thread, because certain platforms
    (OS X) don't allow execv to be called in a child thread very well.
    """
    args = sys.argv[:]
    # self.log('Re-spawning %s' % ' '.join(args))
    args.insert(0, sys.executable)
    if sys.platform == 'win32':
        args = ['"%s"' % arg for arg in args]

    os.chdir(_startup_cwd)
    os.execv(sys.executable, args)


def init_checkers(pcc):
    supervisor = Supervisor()
    supervisor.add_check_task(pcc.check_status)
    supervisor.add_check_task(pcc.hub.fileHandler.check_file)
    supervisor.add_check_task(pcc.send_online_devices, interval=0.5)
    supervisor.add_check_task(pcc.adjust_interval)
    supervisor.add_check_task(pcc.send_statistics, interval=0.5)
    supervisor.start()
    return supervisor


if args.direct:
    print('PCC starts in direct-mode.')

    # cve_conf.local_cfg = get_local_cfg()
    hub = Hub(uniconf=cve_conf, direct_cfg=sys.argv[2])
    pcc = PCC(hub, ipm=True, replay=False, uniconf=cve_conf)
    # hub.start()
    pcc.start()

elif args.headless:
    print('PCC starts in headless-mode.')

    hub = Hub(headless=True)
    hub.start()
    pcc = HeadlessPCC(hub)

    t = Thread(target=pcc.start)
    t.start()
    # hub.fileHandler.start_rec()
    # pcc.start()

    from tornado.web import Application, RequestHandler, StaticFileHandler
    from tornado.ioloop import IOLoop

    class IndexHandler(RequestHandler):
        def post(self):
            action = self.get_body_argument('action')
            if action:
                if 'start' in action:
                    if not hub.fileHandler.recording:
                        hub.fileHandler.start_rec()
                        print(hub.fileHandler.recording)
                        self.write({'status': 'ok', 'action': action, 'message': 'start recording'})
                    else:
                        self.write({'status': 'ok', 'message': 'already recording', 'action': action})
                elif 'stop' in action:
                    if not hub.fileHandler.recording:
                        self.write({'status': 'ok', 'message': 'not recording', 'action': action})
                    else:
                        hub.fileHandler.stop_rec()
                        print(hub.fileHandler.recording)
                        self.write({'status': 'ok', 'action': action, 'message': 'stop recording'})
                elif 'check' in action:
                    mess = 'recording' if hub.fileHandler.recording else 'not recording'
                    self.write({'status': 'ok', 'action': action, 'message': mess})
                elif 'image' in action:
                    img = hub.fileHandler.get_last_image()
                    img = cv2.imdecode(np.fromstring(img, np.uint8), cv2.IMREAD_COLOR)
                    if img is None:
                        # print('pcc', img)
                        # img = cv2.imdecode(np.fromstring(img, np.uint8), cv2.IMREAD_COLOR)
                        img = cv2.imread("./web/statics/jpg/160158-1541059318e139.jpg", cv2.IMREAD_COLOR)

                    base64_str = cv2.imencode('.jpg', img)[1].tostring()
                    base64_str = base64.b64encode(base64_str).decode()
                    self.write({'status': 'ok', 'action': action, 'message': 'get image', 'data': base64_str})
                else:
                    self.write({'status': 'ok', 'message': 'unrecognized action', 'action': action})
            else:
                # self.hub.fileHandler.stop_rec()
                self.write({'status': 'error', 'message': 'not action', 'action': None})

        def get(self):
            self.render("web/index.html")


    app = Application([
        (r'/', IndexHandler),
        (r"/static/(.*)", StaticFileHandler, {"path": "web/statics"}),
    ], debug=False)
    app.listen(9999)
    IOLoop.instance().start()

elif args.web:  # start webui PCC
    # from video_server import PccServer, ctrl_q
    import video_server
    video_server.set_local_path(local_cfg.log_root)
    print('PCC starts in webui mode. architect:', machine_arch)
    server = video_server.PccServer()
    server.start()
    hub = Hub(uniconf=cve_conf)

    pcc = PCC(hub, ipm=True, replay=False, uniconf=cve_conf, auto_rec=False, to_web=server)
    pcc_thread = Thread(target=pcc.start, name='pcc_thread')
    hub.start()

    # print('-----------------------------------------------------------------------', os.getpid())
    sup = init_checkers(pcc)
    # sup.add_check_task(list_recorded_data)
    pcc_thread.start()
    while True:
        if pcc.stuck_cnt > 10:
            print('pcc stuck count:', pcc.stuck_cnt)
            print('PCC stuck. restarting now.')
            respawn()
        if not video_server.ctrl_q.empty():
            ctrl = video_server.ctrl_q.get()
            if ctrl['action'] == 'control':
                key = None
                if ctrl.get('cmd') == 'pause':
                    key = 32
                elif ctrl.get('cmd') == 'start':
                    pass
                elif ctrl.get('cmd') == 'reset':
                    pcc.control(ord('q'))
                    # hub = Hub(uniconf=cve_conf)
                    pcc = PCC(hub, ipm=True, replay=False, uniconf=cve_conf, auto_rec=False, to_web=server)
                    pcc_thread = Thread(target=pcc.start, name='pcc_thread')
                    pcc_thread.start()
                elif ctrl.get('cmd') == 'respawn':

                    hub.close()
                    time.sleep(2)
                    pcc.control(ord('q'))
                    time.sleep(2)
                    server.terminate()
                    server.join()
                    # time.sleep(5)
                    print(bcl.WARN+'CVE processes terminated, now respawn.'+bcl.ENDC)
                    respawn()
                else:
                    key = ord(ctrl['cmd'].lower())

                if key is not None:
                    pcc.control(key)
            elif ctrl['action'] == 'replay':
                pcc.control(ord('q'))
                print('---------------------------------------------------------\n'
                      'pcc exited\n'
                      '----------------------------------------------------------')
                rlog = os.path.join(local_cfg.log_root, ctrl['obj'], 'log.txt')
                from pcc_replay import LogPlayer, prep_replay
                r_sort, cve_conf = prep_replay(rlog, ns=True)
                replayer = LogPlayer(r_sort, cve_conf, ratio=0.2, start_frame=0, loop=True)
                pcc = PCC(replayer, replay=True, rlog=r_sort, ipm=True, uniconf=cve_conf, to_web=server)
                replayer.start()
                pcc_thread = Thread(target=pcc.start, name='pcc_thread')
                pcc_thread.start()
                pass
            elif ctrl['action'] == 'analyze':
                pass

            elif ctrl['action'] == 'delete':
                dir_path = os.path.join(local_cfg.log_root, ctrl['obj'])
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                    print("deleted {} from web control.".format(ctrl['obj']))
                    video_server.send_records()

        else:
            time.sleep(0.1)

else:  # normal standalone PCC
    print('PCC starts in normal mode.')
    # cve_conf = load_cfg(args.cfg_path)
    # local_cfg = get_local_cfg()
    if args.auto:
        auto_rec = True
    else:
        auto_rec = False
    hub = Hub(uniconf=cve_conf)
    pcc = PCC(hub, ipm=False, replay=False, uniconf=cve_conf, auto_rec=auto_rec)
    hub.start()
    sup = init_checkers(pcc)
    pcc.start()
    # pcc.join()
