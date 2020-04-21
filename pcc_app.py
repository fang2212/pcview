import sys
import os
from config.config import load_cfg, dic2obj
import argparse
import json
import cv2

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

if args.direct:
    print('PCC starts in direct-mode.')
    from pcc import *

    # cve_conf.local_cfg = get_local_cfg()
    hub = Hub(uniconf=cve_conf, direct_cfg=sys.argv[2])
    pcc = PCC(hub, ipm=True, replay=False, uniconf=cve_conf)
    pcc.start()

elif args.headless:
    print('PCC starts in headless-mode.')
    from pcc import *
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

elif args.web:
    print('PCC starts in webui mode.')
    from pcc import *
    hub = Hub(uniconf=cve_conf)
    pcc = PCC(hub, ipm=False, replay=False, uniconf=cve_conf, auto_rec=False, to_web=True)
    pcc.start()

else:
    print('PCC starts in normal mode.')
    # cve_conf = load_cfg(args.cfg_path)
    # local_cfg = get_local_cfg()
    if args.auto:
        auto_rec = True
    else:
        auto_rec = False
    from pcc import *
    hub = Hub(uniconf=cve_conf)
    pcc = PCC(hub, ipm=False, replay=False, uniconf=cve_conf, auto_rec=auto_rec)
    pcc.start()
