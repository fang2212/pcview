import sys
import os
from config.config import load_cfg, get_local_cfg

local_path = os.path.split(os.path.realpath(__file__))[0]
# print('local_path:', local_path)
os.chdir(local_path)

# load_cfg(sys.argv[1])

if len(sys.argv) == 1:
    sys.argv.append('config/cfg_lab_suzhou.json')

if '--direct' in sys.argv:
    print('direct mode.')
    from pcc import *
    hub = Hub(direct_cfg=sys.argv[2])
    pcc = PCC(hub, ipm=True, replay=False)
    pcc.start()

elif '--headless' in sys.argv:
    print('headless mode.')
    configs, installs, runtime = load_cfg(sys.argv[1])
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

else:
    print('normal mode.')
    cve_conf = load_cfg(sys.argv[1])
    local_cfg = get_local_cfg()
    from pcc import *
    hub = Hub(uniconf=cve_conf)
    pcc = PCC(hub, ipm=False, replay=False, uniconf=cve_conf)
    pcc.start()
