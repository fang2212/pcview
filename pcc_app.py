import sys
import os
from config.config import load_cfg, dic2obj
import argparse
import json
import cv2
from pcc import *
from tools.mytools import Supervisor
import shutil

local_path = os.path.split(os.path.realpath(__file__))[0]
# print('local_path:', local_path)
os.chdir(local_path)

cfgfile = 'config/cfg_lab.json'

parser = argparse.ArgumentParser(description="process CVE log.")
parser.add_argument('cfg_path', nargs='?', default=cfgfile)
parser.add_argument('-o', '--output', default=None)
parser.add_argument('-d', '--direct', default=None)
parser.add_argument('-hl', '--headless', help='headless mode', action="store_true")
parser.add_argument('-a', '--auto', help='auto recording', action="store_true")
parser.add_argument('-w', '--web', help='web ui', action="store_true")
# load_cfg(sys.argv[1])

args = parser.parse_args()

# if len(sys.argv) == 1:
#     sys.argv.append(cfgfile)

local_cfg = dic2obj(json.load(open('config/local.json')))
opath = args.output or local_cfg.log_root
local_cfg.log_root = opath

cve_conf = load_cfg(args.cfg_path)
cve_conf.local_cfg = local_cfg


def init_checkers(pcc):
    supervisor = Supervisor()
    supervisor.add_check_task(pcc.check_status)
    supervisor.add_check_task(pcc.hub.fileHandler.check_file)
    supervisor.add_check_task(pcc.send_online_devices)
    supervisor.start()
    return supervisor


if args.direct:
    print('PCC starts in direct-mode.')

    # cve_conf.local_cfg = get_local_cfg()
    hub = Hub(uniconf=cve_conf, direct_cfg=sys.argv[2])
    pcc = PCC(hub, ipm=True, replay=False, uniconf=cve_conf)
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
    print('PCC starts in webui mode.')
    hub = Hub(uniconf=cve_conf)

    server = video_server.PccServer()
    pcc = PCC(hub, ipm=False, replay=False, uniconf=cve_conf, auto_rec=False, to_web=server)
    hub.start()
    server.start()
    # print('-----------------------------------------------------------------------', os.getpid())
    sup = init_checkers(pcc)
    # sup.add_check_task(list_recorded_data)
    pcc.start()
    while True:
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
                    pcc = PCC(hub, ipm=False, replay=False, uniconf=cve_conf, auto_rec=False, to_web=server)
                    pcc.start()
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
                pcc.start()
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
