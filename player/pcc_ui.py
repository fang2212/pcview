import time
from datetime import datetime

import cv2
import numpy as np
from math import *

# from config.config import install
from player.ui import BaseDraw, pack, logodir, CVColor, FlatColor
from tools.geo import gps_bearing, gps_distance
from tools.transform import Transform


class InfoCard(object):
    pos_x = 0
    pos_y = 0
    width = 0
    height = 0
    buffer = {}
    ts = 0


class Player(object):
    """图片播放器"""

    def __init__(self, uniconf):
        self.overlook_background_image = cv2.imread(pack(logodir, 'back.png'))
        self.circlesmall_image = cv2.imread(pack(logodir, 'circlesmall.tif'))
        self.sectorwide_image = cv2.imread(pack(logodir, 'sectorwide.tif'))
        self.sectorthin_image = cv2.imread(pack(logodir, 'sectorthin.tif'))
        self.car_image = cv2.imread(pack(logodir, 'car.tif'))
        self.overlook_othercar_image = cv2.imread(pack(logodir, 'othercar.tif'))
        self.overlook_beforecar_image = cv2.imread(pack(logodir, 'before.tif'))
        self.transform = Transform(uniconf)
        self.cfg = uniconf

        self.video_streams = {'video': {}}
        self.img_width = 1280
        self.img_height = 720
        self.indent = 160
        self.columns = {'video': {'indent': 0, 'y0': 0, 'h': 1000, 'buffer': {}, 'ts': 0}}
        self.param_bg_width = 160
        self.next_patch_x = 160
        self.next_patch_y = 0
        self.ts_now = 0
        self.rtk = {}

        self.start_time = datetime.now()
        self.cipv = 0
        self.pxs = None

        self.color_seq = [CVColor.White, CVColor.Red, CVColor.Green, CVColor.deeporange, CVColor.purple,
                          CVColor.Blue, CVColor.LightBlue, CVColor.Black, CVColor.Grass]

        self.color_obs = {
            "a1j": (193, 182, 255),
            "a1j_fusion": (59, 59, 238),
            "a1j_vision": (193, 182, 255),
            "ars410": FlatColor.peach,
            "bosch_mrr": FlatColor.yellow,
            "d1_fusion": FlatColor.violet,
            "gs4_debug": FlatColor.pink,
            "j2": FlatColor.carrot,
            "j2_fusion": FlatColor.light_green,
            "q4_100": FlatColor.turquoise,
            'anc': FlatColor.carrot,
            'ars': FlatColor.emerald,
            'ctlrr': FlatColor.alizarin,
            'default': FlatColor.clouds,
            'esr': FlatColor.alizarin,
            'gps': FlatColor.clouds,
            'ifv300': CVColor.Blue,
            'ifv300_vision': (255, 144, 30),
            'ifv300_fusion': CVColor.Blue,
            'lmr': FlatColor.emerald,
            'mbq3': CVColor.Blue,
            'mbq3_vision': (255, 144, 30),
            'mbq3_fusion': CVColor.Blue,
            'mbq4': FlatColor.turquoise,
            'rtk': FlatColor.sun_flower,
            'sta77': FlatColor.wet_asphalt,
            "wsk": FlatColor.pink,
            'x1': FlatColor.amethyst,
            'x1_fusion': CVColor.Red,
            'x1_fusion_cam': FlatColor.dark_red,
            'x1j': FlatColor.amethyst,
            'xyd2': FlatColor.Blue,
        }

        self.detection_color = {
            'Unknown': 'fail',
            'SingleTrack': 'pass',
            'MultipleTrack': 'pass',
            'Vision Only': 'pass',
            'Radar And Vision': 'pass'
        }

        self.param_bg_width = 160

        # for col in self.columns:
        #     if len(col) == 0:
        #         del self.columns[col]
        # print(self.columns)

    def add_info_column(self, msg_type):
        if len(msg_type) == 0:
            # self.columns.remove(col)
            # del self.columns[i]
            return
        else:
            self.columns[msg_type] = {'indent': self.next_patch_x, 'y0': self.next_patch_y}
            # if 'rtk' in msg_type:
            #     self.indent += 300
            # else:
            self.next_patch_x += 160
            for src_type in self.color_obs:
                if msg_type.split('.')[0] == src_type:
                    self.columns[msg_type]['color'] = self.color_obs[src_type]
            self.columns[msg_type]['buffer'] = dict()
            self.columns[msg_type]['ts'] = 0
            self.columns[msg_type]['h'] = 1000
        # self.param_bg_width = self.next_patch_x + 20
        # if self.next_patch_x > self.img_width:


    def get_indent(self, source):
        if source in self.columns:
            return self.columns[source]['indent']
        else:
            self.add_info_column(source)
            return self.columns[source]['indent']

    def show_dist_mark_ipm(self, img):
        show_range = 201
        for i in range(0, show_range, 1):
            if i % 20 == 0:
                p1 = self.transform.trans_gnd2ipm(i, -10)
                p2 = self.transform.trans_gnd2ipm(i, 10)
                BaseDraw.draw_line(img, p1, p2, color_type=CVColor.Midgrey, thickness=1)
                BaseDraw.draw_text(img, '{}m'.format(i), self.transform.trans_gnd2ipm(i - 1, 10), 0.3, CVColor.White, 1)

        for i in [-4 * 0.5, 4 * 0.5]:
            p1 = self.transform.trans_gnd2ipm(-10, i)
            p2 = self.transform.trans_gnd2ipm(show_range, i)
            BaseDraw.draw_line(img, p1, p2, color_type=CVColor.LightRed, thickness=1)
            BaseDraw.draw_text(img, '{}m'.format(i), self.transform.trans_gnd2ipm(2, i - 1), 0.3, CVColor.White, 1)

        for i in [-4 * 2.5, -4 * 1.5, 4 * 1.5, 4 * 2.5]:
            p1 = self.transform.trans_gnd2ipm(-10, i)
            p2 = self.transform.trans_gnd2ipm(show_range, i)
            BaseDraw.draw_line(img, p1, p2, color_type=CVColor.Midgrey, thickness=1)
            BaseDraw.draw_text(img, '{}m'.format(i), self.transform.trans_gnd2ipm(2, i - 1), 0.3, CVColor.White, 1)

    def show_parameters_background(self, img, rect):
        """左上角参数背景图"""
        BaseDraw.draw_alpha_rect(img, rect, 0.6, CVColor.Black)

    def show_obs(self, img, obs, thickness=2):
        try:
            indent = self.get_indent(obs['source'])
        except Exception as e:
            print('Error indent', obs)
            return
        source = obs['source'].split('.')[0]
        sensor = obs.get('sensor') or source
        color = obs.get("color") or self.color_obs.get(source) or self.color_obs['default']

        width = obs.get('width')
        width = width or 0.3
        height = obs.get('height')
        # print(obs['source'], obs['class'])
        height = height or width
        if obs.get('class') == 'pedestrian' or obs.get('class') == 'PEDESTRIAN':
            height = 1.6
        # install_para = install[obs['source'].split('.')[0]]

        if 'pos_lon' in obs:
            # x = obs['pos_lon']
            # y = obs['pos_lat']
            if 'pos_lat' not in obs:
                print('no pos_lat', obs)
            x, y = self.transform.compensate_param_rcs(obs['pos_lon'], obs['pos_lat'], sensor)
            dist = (x ** 2 + y ** 2) ** 0.5

        elif 'range' in obs:
            # print(obs['source'].split('.')[0])
            # x, y = self.transform.trans_polar2rcs(obs['angle'], obs['range'], install[obs['source'].split('.')[0]])
            dist = obs['range']
            x, y = self.transform.trans_polar2rcs(obs['angle'], obs['range'], sensor)
        else:
            print('no x dis in obs:', obs)
            return
        dist = max(0.1, dist)
        if dist <= 0 or x <= 0:
            return

        w = self.cfg.installs['video']['fu'] * width / dist
        w = min(600, w)
        # dev = obs.get('source')
        # if dev:
        #     dev = dev.split('.')[0]
        #     print(dev)
        # else:
        #     dev = 'default'
        # print(x, y)
        x0, y0 = self.transform.trans_gnd2raw(x, y)

        h = self.cfg.installs['video']['fv'] * height / dist
        x1 = x0 - 0.5 * w
        y1 = y0 - h
        x2 = x1 + w
        y2 = y0
        x1 = int(x1)
        x2 = int(x2)
        y1 = int(y1)
        y2 = int(y2)

        size = max(min(0.5 * 8 / dist, 0.5), 0.28)
        if obs.get('sensor_type') == 'radar':
            w = max(5, min(50, w))
            h = max(5, min(50, h))
            # print(int(x1), int(y1), int(w), width)
            cv2.circle(img, (int(x0), int(y0 - 0.5 * h)), int(w), color, 1)
            # print(x1, y1, x, h)
            BaseDraw.draw_text(img, '{}'.format(obs['id']), (x1 + int(1.4 * w), y1 + int(1.4 * w)), size, color, 1)
        elif obs.get('class') == 'pedestrian':
            if x1 < 0 or y1 < 0 or x2 > img.shape[1] or y2 > img.shape[0]:
                return
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 1)
            BaseDraw.draw_alpha_poly(img, np.array([(x1, y1), (x1, y2), (x2, y2), (x2, y1)]), 0.3, color)
            BaseDraw.draw_text(img, '{}'.format(obs['id']), (x1 - 2, y1 - 4), size, color, 1)
        else:
            BaseDraw.draw_rect_corn(img, (x1, y1), (x2, y2), color, thickness)
            BaseDraw.draw_text(img, '{}'.format(obs['id']), (x1 - 2, y1 - 4), size, color, 1)

        if 'cipo' in obs and obs['cipo']:
            # color = CVColor.Yellow
            self.show_cipo_info(img, obs)
            BaseDraw.draw_up_arrow(img, x0, y0 + 3, color)

        # if 'TTC' in obs:
        #     self.show_ttc(img, obs['TTC'], obs['source'])

    def show_ipm_obs(self, img, obs):
        # print(obs)
        try:
            source = obs['source']
        except Exception as e:
            print('Error, no source in', obs)
            return

        id = obs['id']
        source = obs['source'].split('.')[0]
        if 'pos_lon' in obs:
            # x = obs['pos_lon']
            # y = obs['pos_lat']
            x, y = self.transform.compensate_param_rcs(obs['pos_lon'], obs['pos_lat'], source)
        elif 'range' in obs:
            x, y = self.transform.trans_polar2rcs(obs['angle'], obs['range'], source)
        else:
            print('no distance in obs', obs)
            return

        # j2_fusion的bug，会在0，0坐标中出现假坐标，对其进行屏蔽
        if x == 0 and y == 0:
            return

        u, v = self.transform.trans_gnd2ipm(x, y)

        color = obs.get("color") or self.color_obs.get(source) or self.color_obs['default']

        if 'x1_fusion' in obs['source'] and obs['sensor'] == 'x1':
            color = self.color_obs.get('x1_fusion_cam')
            # print(obs)

        if obs.get('sensor_type') == 'radar':
            cv2.circle(img, (u, v - 8), 8, color, 1)
            BaseDraw.draw_text(img, '{}'.format(id), (u + 10, v - 5), 0.3, color, 1)
            # ESR
            if 'TTC' in obs:
                # for save space, only ttc<7 will be shown on the gui
                if obs['TTC'] < 7:
                    BaseDraw.draw_text(img, '{:.1f}'.format(obs['TTC']), (u - 25, v + 5), 0.3, color, 1)

            # STA 77
            if obs.get('sensor') == 'sta77':
                BaseDraw.draw_text(img, '{:.1f}'.format(x), (u - 40, v + 5), 0.3, color, 1)

            if obs.get('sensor') == 'anc':
                BaseDraw.draw_text(img, '{:.1f}'.format(x), (u - 30, v - 5), 0.3, color, 1)
                BaseDraw.draw_text(img, '{:.1f}'.format(y), (u - 30, v + 5), 0.3, color, 1)

        else:
            if obs.get('class') == 'pedestrian' or obs.get('class') == 'PEDESTRIAN':
                cv2.rectangle(img, (u - 4, v - 16), (u + 4, v), color, 2)
            else:
                cv2.rectangle(img, (u - 8, v - 16), (u + 8, v), color, 2)
            # BaseDraw.draw_text(img, '{}'.format(id), (u - 6, v - 6), 0.3, color, 1)
            BaseDraw.draw_text(img, '{}'.format(id), (u + 10, v - 9), 0.4, color, 1)
            BaseDraw.draw_text(img, '{:.1f}'.format(x), (u + 10, v + 3), 0.4, color, 1)

    def show_lane(self, img, data, color=CVColor.Cyan, style=""):
        """绘制车道线
        Args:
            img: 原始图片
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            width: float 车道线宽度
            color: CVColor 车道线颜色
            :param style: 线条格式，虚线为“dotted”
        """
        max_range = data.get('range')
        min_range = data.get("min_range", 0)
        ratios = (data['a0'], data['a1'], data['a2'], data['a3'])
        source = data['source']
        if max_range == 0:
            return

        if 'j2' in source:
            source = ""

        p = self.transform.getp_ifc_from_poly(ratios, 1, min_range, max_range, sensor=source)
        if not p:
            return

        if style == "dotted":
            for i in range(2, len(p) - 1, 1):
                if i % 3 == 0:
                    BaseDraw.draw_line(img, p[i], p[i + 1], color, 2)
        else:
            for i in range(2, len(p) - 1, 1):
                BaseDraw.draw_line(img, p[i], p[i + 1], color, 2)

            # for now: only mbq4 used
        a0, a1, a2, a3 = ratios
        if abs(a0) < 5:
            x = 12
        else:
            x = 25
        y = a0 + a1 * x + a2 * x ** 2 + a3 * x ** 3

        tx, ty = self.transform.trans_gnd2raw(x, y)
        text_step = 15
        if 'type_class' in data:
            BaseDraw.draw_text(img, 'class: {}'.format(data['type_class']), (tx - 50, ty), 0.5, color, 1)

        if 'prediction_source' in data:
            BaseDraw.draw_text(img, 'predict: {}'.format(data['prediction_source']), (tx - 50, ty + text_step), 0.5, color, 1)

        if 'probability' in data:
            BaseDraw.draw_text(img, 'prob: ' + str('%.2f' % data['probability']), (tx - 50, ty + text_step * 2),
                               0.5, color, 1)

    def show_tsr(self, img, data):
        x = data.get('pos_lon')
        y = data.get('pos_lat')
        h = data.get('pos_hgt')
        u, v = self.transform.trans_gnd2raw(x, y, h)
        color = self.color_obs.get(data['sensor']) or self.color_obs['default']
        cv2.rectangle(img, (u - 8, v - 16), (u + 8, v), color, 2)

    def show_text_info(self, source, height, text, style='normal', size=None):
        if style is None:
            style = 'warning'
        self.get_indent(source)
        self.columns[source]['buffer'][height] = {'text': text, 'style': style, 'size': size}
        # print(source, height, text)

    def update_column_ts(self, source, ts):
        if not source:
            return
        self.columns[source]['ts'] = ts

    def render_text_info(self, img):
        # self.show_columns(img)
        # print(len(self.columns))
        self.img_height, self.img_width, _ = img.shape
        # print(self.img_width, self.img_height)
        w = 160
        slots = {}
        for i in range(0, self.img_width, w):
            slots[i] = 0
        # smallest_h = 1000
        # print(self.columns)
        # shortest_col = sorted(self.columns, key=lambda x: self.columns[x]['y0'] + self.columns[x]['h'])[0]

        # print('shortest col:', shortest_col)
        # shortest_col = None
        next_patch_x = 0
        next_patch_y = 0
        for idx, col in enumerate(self.columns):
            indent = sorted(slots, key=lambda x: slots[x])[0]
            y0 = slots[indent]
            entry = self.columns[col]
            # indent = next_patch_x
            # y0 = next_patch_y
            h = max(self.columns[col]['buffer']) + 4 if self.columns[col]['buffer'] else 24
            h = 24 if h == 0 else h
            self.columns[col]['indent'] = indent
            self.columns[col]['y0'] = y0
            self.columns[col]['h'] = h
            slots[indent] = y0 + h + 2
            # if idx+2 <= int(self.img_width/w):
            #     next_patch_x += w
            #     next_patch_y = 0
            # else:
            #     next_patch_y = shortest_y
            #     next_patch_x = shortest_x
                # print('replace patch', idx, col, indent, y0, w, h)
            # if h + y0 < smallest_h:
            #     smallest_h = h + y0
            #     shortest_col = col

            # if col is not 'video':
            #     color_lg = self.columns[col].get('color')
            #     if color_lg is not None:
            #         cv2.rectangle(img, (indent + 1, 1), (indent + 159, 24), self.columns[col]['color'], -1)
            # print(idx, col, indent, y0, w, h)
            self.show_parameters_background(img, (indent, y0, w if w <= self.img_width else self.img_width, h))

            if col != 'video':
                color_lg = self.columns[col].get('color')
                if color_lg is None:
                    color_lg = CVColor.LightGray

                cv2.rectangle(img, (indent + 1, y0 + 1), (indent + 19, y0 + 24), color_lg, -1)
                cv2.rectangle(img, (indent, y0), (indent + w - 2, y0 + h), color_lg, 2)
            if 'ifv300' in col:
                BaseDraw.draw_text(img, 'q3', (indent + 22, y0 + 20), 0.5, CVColor.Cyan, 1)
            else:
                if '.can' in col:
                    fields = col.split('.')
                    devno = '.'.join(fields[:3])
                    BaseDraw.draw_text(img, fields[-1], (indent + 22, y0 + 12), 0.4, CVColor.Cyan, 1)
                    BaseDraw.draw_text(img, devno, (indent + 22, y0 + 24), 0.4, CVColor.Cyan, 1)
                else:
                    title = col
                    BaseDraw.draw_text(img, title, (indent + 22, y0 + 20), 0.5, CVColor.Cyan, 1)
            dt = self.ts_now - self.columns[col]['ts']

            if dt > 999:
                delay_ms = ">+999s"
            elif dt < -999:
                delay_ms = "<-999s"
            elif dt >= 1 or dt <= -1:
                delay_ms = "{:+4d}s".format(int(dt))
            else:
                delay_ms = '{:>+4d}ms'.format(int(dt * 1000))
            BaseDraw.draw_text(img, delay_ms, (indent + 92, y0 + 20), 0.5, CVColor.White, 1)
            # if col is not 'video':
            #     cv2.rectangle(img, (indent, 0), (indent + 160, 20), self.columns[col]['color'], -1)
            for height in entry['buffer']:
                # print(col, height, entry['buffer'])
                # 字体颜色
                style = entry['buffer'][height]['style']
                style_list = {'normal': None, 'warning': CVColor.Yellow, 'fail': CVColor.Red, 'pass': CVColor.Green}
                if isinstance(style, str) and style_list.get(style):
                    if style in style_list:
                        color = style_list.get(style)
                    else:
                        if style == 'critical':
                            pass
                elif isinstance(style, tuple):
                    color = style
                else:
                    color = CVColor.White

                # 字体大小
                if entry['buffer'][height].get("size"):
                    size = entry['buffer'][height]['size']
                else:
                    line_len = len(entry['buffer'][height]['text'])
                    size = min(0.5 * 16 / line_len, 0.5)
                    size = max(0.24, size)

                BaseDraw.draw_text(img, entry['buffer'][height]['text'], (entry['indent'] + 2, height + y0), size,
                                   color, 1)

    def show_video_info(self, img, data):
        tnow = data['ts']
        if data['source'] not in self.video_streams:
            self.video_streams[data['source']] = {'frame_cnt': data['frame_id'] - 1, 'last_ts': 0, 'ts0': time.time(),
                                                  'fps': 20}
        if tnow == self.video_streams[data['source']]['last_ts']:
            return
        self.show_parameters_background(img, (0, 0, 160, 80))
        BaseDraw.draw_text(img, data['source'], (2, 20), 0.5, CVColor.Cyan, 1)
        dt = self.ts_now - data['ts']
        BaseDraw.draw_text(img, '{:>+4d}ms'.format(int(dt * 1000)), (92, 20), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'frame: {}'.format(data['frame_id']), (2, 40), 0.5, CVColor.White, 1)

        self.video_streams[data['source']]['frame_cnt'] += 1
        # duration = time.time() - self.video_streams[data['source']]['ts0']
        dt = tnow - self.video_streams[data['source']]['last_ts']
        self.video_streams[data['source']]['last_ts'] = tnow
        fps = 1 / dt
        self.video_streams[data['source']]['fps'] = 0.9 * self.video_streams[data['source']]['fps'] + 0.1 * fps
        BaseDraw.draw_text(img, 'fps: {:.1f}'.format(self.video_streams[data['source']]['fps']), (2, 60), 0.5,
                           CVColor.White, 1)
        BaseDraw.draw_text(img,
                           'lost frames: {}'.format(data['frame_id'] - self.video_streams[data['source']]['frame_cnt']),
                           (2, 80), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'dev: {}'.format(data['device']), (2, 100), 0.5, CVColor.White, 1)

    def show_status_info(self, img, source, status_list):
        """
        显示状态栏信息
        style: normal, warning, fail, pass
        """
        show_line = 40          # 显示的行位置，每20像素的高度为一行
        for i in status_list:
            self.show_text_info(source, i.get("height", show_line), i.get("text", ""), i.get("style", "normal"), i.get("size"))
            show_line = i.get("height", show_line) + 20

    def show_frame_id(self, img, source, fn):
        # indent = self.columns['video']['indent']
        # BaseDraw.draw_text(img, 'fid: ' + str(int(fn)), (indent + 2, 40), 0.5, CVColor.White, 1)
        self.show_text_info(source, 40, 'frame: ' + str(int(fn)))

    def show_pinpoint(self, img, pp):
        BaseDraw.draw_text(img, 'Pin: {lat:.8f} {lon:.8f} {hgt:.3f}'.format(**pp), (950, 710), 0.3, CVColor.White, 1)

    def show_frame_cost(self, cost):
        self.show_text_info('video', 80, 'render_cost: {}ms'.format(int(cost * 1000)))

    def show_fps(self, img, source, fps):
        # indent = self.columns['video']['indent']
        # BaseDraw.draw_text(img, 'fps: ' + str(int(fps)), (indent + 2, 60), 0.5, CVColor.White, 1)
        self.show_text_info(source, 60, 'fps: ' + str(int(fps)))

    def show_datetime(self, img, ts=None):
        # indent = self.columns['video']['indent']
        if ts is None:
            ta = datetime.now()
        else:
            ta = time.localtime(ts)

        FORMAT = '%Y/%m/%d'
        date = time.strftime(FORMAT, ta)
        FORMAT = '%H:%M:%S'
        time_ = time.strftime(FORMAT, ta)
        # BaseDraw.draw_text(img, '{}'.format(date), (indent + 2, 100), 0.5, CVColor.White, 1)
        # BaseDraw.draw_text(img, '{}'.format(time_), (indent + 2, 120), 0.5, CVColor.White, 1)
        self.show_text_info('video', 100, '{}'.format(date))
        self.show_text_info('video', 120, '{}'.format(time_))

    def show_ttc(self, img, ttc, source):
        # indent = self.columns[source]['indent']
        # BaseDraw.draw_text(img, 'TTC:' + '{:.2f} s'.format(ttc), (indent + 2, 40), 0.5, CVColor.Cyan, 1)
        self.show_text_info(source, 40, 'TTC:' + '{:.2f} s'.format(ttc))

    def show_veh_speed(self, img, speed, source):
        # indent = self.get_indent(source)
        # BaseDraw.draw_text(img, '{:.1f} km/h'.format(speed), (indent + 2, 40), 0.5, CVColor.White, 1)
        self.show_text_info(source, 40, '{:.1f} km/h'.format(speed))

    def show_yaw_rate(self, img, yr, source):
        # indent = self.get_indent(source)
        yr_deg = yr * 57.3
        # BaseDraw.draw_text(img, '%.1f' % yr_deg + ' deg/s', (indent + 2, 60), 0.5, CVColor.White, 1)
        self.show_text_info(source, 60, '{:.1f}deg/s'.format(yr_deg))

    def show_accel(self, img, acc, source):
        # indent = self.get_indent(source)
        # yr_deg = yr * 57.3
        # BaseDraw.draw_text(img, '%.1f' % yr_deg + ' deg/s', (indent + 2, 60), 0.5, CVColor.White, 1)
        self.show_text_info(source, 80, '{:.1f}m/s^2'.format(acc))

    def show_q3_veh(self, img, speed, yr):
        BaseDraw.draw_text(img, 'q3spd: ' + str(int(speed * 3.6)), (2, 120), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'q3yr: ' + '%.4f' % yr, (2, 140), 0.5, CVColor.White, 1)
        # self.show_text_info(source, 40, )

    def show_recording(self, img, info):
        if info == 0:
            self.show_text_info('video', 140, '               ')
            self.show_text_info('video', 160, '               ')
            return
        time_passed = time.time() - info
        self.show_text_info('video', 140, '***[REC]***', CVColor.Red)
        self.show_text_info('video', 160, 'Rec time: {:.2f}s'.format(time_passed))
        # BaseDraw.draw_text(img, 'Recording... ', (2, 700), 0.5, CVColor.White, 1)
        # BaseDraw.draw_text(img, 'time elapsed: {:.2f}s'.format(time_passed), (2, 712), 0.5, CVColor.White, 1)

    def show_marking(self, img, start_time):
        time_passed = time.time() - start_time
        BaseDraw.draw_text(img, 'Marking time: {:.2f}s'.format(time_passed), (100, 680), 3, CVColor.Green, 3)

    def show_replaying(self, img, dts):
        time_passed = dts
        self.show_text_info('video', 140, 'Replaying... ', CVColor.Red)
        self.show_text_info('video', 160, 'replay time: {:.2f}s'.format(time_passed))
        # BaseDraw.draw_text(img, 'Replaying... ', (2, 700), 0.5, CVColor.White, 1)
        # BaseDraw.draw_text(img, 'replay time: {:.2f}s'.format(time_passed), (2, 712), 0.5, CVColor.White, 1)

    def show_version(self, img, cfg):
        if cfg.runtime.get('build_time'):
            img_h = img.shape[0]
            # BaseDraw.draw_text(img, cfg.runtime.get('build_time'), (2, img_h-20), 0.5, CVColor.White, 1)
            BaseDraw.draw_text(img, cfg.runtime.get('git_version') + ' ' + cfg.runtime.get('build_time'), (2, img_h - 6), 0.3, CVColor.White, 1)

    def show_cipo_info(self, img, obs):
        try:
            indent = self.get_indent(obs['source'])
        except Exception as e:
            print('Error:', obs)
            return

        color = self.color_obs['rtk']
        line = 100
        style = 'normal'
        if 'x1_fusion' in obs['source'] and obs['sensor'] == 'x1':
            line = 160
            style = self.color_obs.get(obs['source'])
            self.show_text_info(obs['source'], line, 'CIPV_cam: {}'.format(obs['id']), style)
        elif obs.get("sensor") == "a1j_fusion" or obs.get("sensor") == "ifv300_fusion":
            line = 180
            self.show_text_info(obs['source'], line, 'CIPV_cam: {}'.format(obs['id']), style)
        elif obs.get('class') == 'pedestrian':
            line = 40
            self.show_text_info(obs['source'], line, 'CIPPed: {}'.format(obs['id']))
        elif obs.get('class') == 'object':
            self.show_text_info(obs['source'], line, 'CIPO: {}'.format(obs['id']))
        else:
            color = obs.get("color") or self.color_obs['rtk']
            self.show_text_info(obs['source'], line, 'CIPVeh: {}'.format(obs['id']))

        if "detection_sensor" in obs:
            self.show_text_info(obs['source'], 60, '{}'.format(obs['detection_sensor']), self.detection_color.get(obs.get("detection_sensor")))
        if 'TTC' in obs:
            self.show_text_info(obs['source'], line + 20, 'TTC: ' + '{:.2f}s'.format(obs['TTC']), style)
        dist = obs.get('pos_lon') if 'pos_lon' in obs else obs['range']
        angle = obs.get('angle') if 'angle' in obs else atan2(obs['pos_lat'], obs['pos_lon']) * 180 / pi
        # BaseDraw.draw_text(img, 'range: {:.2f}'.format(dist), (indent + 2, line + 40), 0.5, CVColor.White, 1)
        self.show_text_info(obs['source'], line + 40, 'R/A: {:.2f} / {:.2f}'.format(dist, angle), style)
        BaseDraw.draw_up_arrow(img, indent + 100, line - 12, color, 6)

    def show_heading_horizen(self, img, rtk):
        heading = rtk.get('yaw')
        pitch = rtk.get('pitch')
        # print(pitch)
        if not heading:
            return
        hfov = 90.0
        vfov = 60.0
        dyaw = self.cfg.installs['rtk']['yaw'] - self.cfg.installs['video']['yaw']
        dpitch = self.cfg.installs['rtk']['pitch'] - self.cfg.installs['video']['pitch']
        # vbias = (pitch - dpitch) * self.cfg.installs['video']['cv'] / (vfov / 2)
        vbias = self.cfg.installs['video']['pitch'] * self.cfg.installs['video']['cv'] / (vfov / 2)
        h = int(img.shape[0] / 2 - vbias)
        # h = int(img.shape[0] / 2)
        w = img.shape[1]
        bias = w * dyaw / hfov
        hc = int(w / 2 + bias)
        BaseDraw.draw_line(img, (0, h), (w, h), CVColor.Grey, 1)
        BaseDraw.draw_line(img, (hc, h - 30), (hc, h + 10), CVColor.White, 1)
        BaseDraw.draw_line(img, (hc + 5, h - 30), (hc - 5, h - 30), CVColor.White, 1)
        BaseDraw.draw_text(img, '{:.1f}'.format(heading), (hc - 14, h - 32), 0.4, CVColor.White, 1)
        heading_start = heading - hfov / 2 - dyaw
        heading_end = heading + hfov / 2 - dyaw
        self.pxs = []
        for deg in range(int(heading_start), 360):
            px = int((deg - heading_start) * w / hfov)
            if deg < 0.0:
                deg = 360 + deg
            if deg > 360.0:
                deg = deg - 360.0
            self.pxs.append((px, deg))

        for px, deg in self.pxs:
            if deg == 0:
                BaseDraw.draw_line(img, (px, h - 12), (px, h), CVColor.White, 1)
                BaseDraw.draw_text(img, 'N', (px - 5, h - 12), 0.5, CVColor.White, 1)
            elif deg == 90:
                BaseDraw.draw_line(img, (px, h - 12), (px, h), CVColor.White, 1)
                BaseDraw.draw_text(img, 'E', (px - 5, h - 12), 0.5, CVColor.White, 1)
            elif deg == 180:
                BaseDraw.draw_line(img, (px, h - 12), (px, h), CVColor.White, 1)
                BaseDraw.draw_text(img, 'S', (px - 5, h - 12), 0.5, CVColor.White, 1)
            elif deg == 90:
                BaseDraw.draw_line(img, (px, h - 12), (px, h), CVColor.White, 1)
                BaseDraw.draw_text(img, 'W', (px - 5, h - 12), 0.5, CVColor.White, 1)
            elif deg % 5 == 0:
                BaseDraw.draw_line(img, (px, h - 10), (px, h), CVColor.White, 1)
                BaseDraw.draw_text(img, '{}'.format(deg), (px - 10, h - 10), 0.4, CVColor.White, 1)
            else:
                BaseDraw.draw_line(img, (px, h - 5), (px, h), CVColor.Grey, 1)

    def show_track_gnd(self, img, rtk):
        trk_gnd = rtk.get('trk_gnd')
        speed = rtk.get('hor_speed')
        if not self.pxs or speed < 2:
            return
        trk_gnd = trk_gnd - 180.0
        if trk_gnd > 360:
            trk_gnd = trk_gnd - 360
        if trk_gnd < 0:
            trk_gnd = trk_gnd + 360
        hfov = 90.0
        dyaw = self.cfg.installs['video']['yaw']
        h = int(img.shape[0] / 2)
        w = img.shape[1]
        bias = w * dyaw / hfov

        if self.pxs[0][1] > 360 - hfov:
            begin = self.pxs[0][1] - 360
        else:
            begin = self.pxs[0][1]
        px = (trk_gnd - begin) * w / hfov
        hc = int(px + bias)
        BaseDraw.draw_line(img, (hc, h - 44), (hc, h + 10), CVColor.White, 1)
        BaseDraw.draw_line(img, (hc + 5, h - 44), (hc - 5, h - 44), CVColor.White, 1)
        BaseDraw.draw_text(img, '{:.1f}'.format(trk_gnd), (hc - 14, h - 46), 0.4, CVColor.White, 1)

    def show_warning(self, img, data):
        sensor = data.get('sensor') or data['source'].split('.')[0]
        color = self.color_obs.get(sensor)
        if not color:
            color = self.color_obs['default']

        # width = 3.5
        # height = 1.6
        # x, y = data['pos_lon'], 0
        # dist = (x ** 2 + y ** 2) ** 0.5
        # dist = max(0.1, dist)
        # if dist <= 0 or x <= 0:
        #     return
        #
        # w = self.cfg.installs['video']['fu'] * width / dist
        # w = int(w)
        #
        # x0, y0 = self.transform.trans_gnd2raw(x, y)
        #
        # h = int(self.cfg.installs['video']['fv'] * height / dist)
        # x1 = int(x0 - 0.5 * w)
        # y1 = int(y0 - h)
        # x2 = int(x1 + w)
        # y2 = int(y1 + h)
        #
        # size = max(min(0.5 * 8 / dist, 0.5), 0.28)

        # BaseDraw.draw_rect_corn(img, (x1, y1), (x2, y2), color, 1)
        # BaseDraw.show_stop_wall(img, (x1, y1), (x2, y2), color, 1)
        # BaseDraw.draw_text(img, 'x: {:.2f}m TTC: {:.2f}'.format(x, data['TTC']), (x1 - 2, y1 - 4), size, color, 1)

        # BaseDraw.draw_alpha_rect(img, (x1, y1, w, h), 0.8, CVColor.Red)
        if 'ldw_left' in data:
            self.show_text_info(data['source'], 40, 'ldw_left: {}'.format(data['ldw_left']))
        if 'ldw_right' in data:
            self.show_text_info(data['source'], 60, 'ldw_right: {}'.format(data['ldw_right']))
        if 'fcw_level' in data:
            self.show_text_info(data['source'], 80, 'fcw_level: {}'.format(data['fcw_level']))
        if "TTC" in data:
            self.show_text_info(data['source'], 100, 'TTC: {:.2f} s'.format(data['TTC']))
        if 'pos_lon' in data:
            self.show_text_info(data['source'], 120, 'x: {:.1f} m'.format(data['pos_lon']))
        if 'vel_lat' in data:
            self.show_text_info(data['source'], 140, 'vel_f: {:.1f} m'.format(data['vel_lon']))

    def _show_drtk(self, img, rtk):
        # print(rtk)
        indent = self.get_indent(rtk['source'])
        if rtk['updated']:
            color = CVColor.White
        else:
            color = CVColor.Grey
        BaseDraw.draw_text(img, 'rtkSt: {}'.format(rtk['rtkst']), (indent + 142, 40), 0.5, color, 1)
        BaseDraw.draw_text(img, 'lat: {:.8f}'.format(rtk['lat']), (indent + 142, 60), 0.5, color, 1)
        BaseDraw.draw_text(img, 'lon:{:.8f}'.format(rtk['lon']), (indent + 142, 80), 0.5, color, 1)
        BaseDraw.draw_text(img, 'hgt: {:.3f}'.format(rtk['hgt']), (indent + 142, 100), 0.5, color, 1)

        BaseDraw.draw_text(img, 'oriSt: {}'.format(rtk['orist']), (indent + 2, 40), 0.5, color, 1)
        BaseDraw.draw_text(img, 'yaw: {:.2f}'.format(rtk['yaw']), (indent + 2, 60), 0.5, color, 1)
        BaseDraw.draw_text(img, 'pitch: {:.2f}'.format(rtk['pitch']), (indent + 2, 80), 0.5, color, 1)
        BaseDraw.draw_text(img, 'len: {:.3f}'.format(rtk['length']), (indent + 2, 100), 0.5, color, 1)
        BaseDraw.draw_text(img, 'delay: {:.4f}'.format(rtk['ts'] - rtk['ts_origin']), (indent + 2, 120), 0.5, color, 1)
        vel = (rtk['velN'] ** 2 + rtk['velE'] ** 2) ** 0.5
        BaseDraw.draw_text(img, '{:.2f}km/h'.format(vel * 3.6), (indent + 142, 120), 0.5, color, 1)
        if 'sat' in rtk:
            BaseDraw.draw_text(img, '#rtk:{}/{} #ori:{}/{}'.format(rtk['sat'][1], rtk['sat'][0], rtk['sat'][5],
                                                                   rtk['sat'][4]), (indent + 50, 20), 0.5, color, 1)

    def show_target(self, img, target, host):
        if not target or not host:
            return
        indent = self.get_indent(target['source'])

        range, angle = self._calc_relatives(target, host)
        x, y = self.transform.trans_polar2rcs(angle, range, 'rtk')
        if x == 0:
            x = 0.001
        width = 0.5
        height = 0.5
        ux, uy = self.transform.trans_gnd2raw(x, y, host['hgt'] - target['hgt'] + self.cfg.installs['video']['height'] -
                                              self.cfg.installs['rtk']['height'])
        w = 1200 * width / x
        if w > 50:
            w = 50

        h = w

        p1 = int(ux - 0.5 * w), int(uy)
        p2 = int(ux + 0.5 * w), int(uy)
        p3 = int(ux), int(uy - 0.5 * h)
        p4 = int(ux), int(uy + 0.5 * h)

        if angle > 90 or angle < -90:
            BaseDraw.draw_text(img, 'RTK target in behind', (int(ux + 4), int(uy - 4)), 0.6, CVColor.White, 1)
            return
        # cv2.line(img, p1, p2, CVColor.Green if target['rtkst'] >= 48 else CVColor.Grey, 2)
        # cv2.line(img, p3, p4, CVColor.Green if host['rtkst'] >= 48 else CVColor.Grey, 2)

        cv2.line(img, p1, p2, CVColor.White, 2)
        cv2.line(img, p3, p4, CVColor.White, 2)

        # BaseDraw.draw_text(img, 'R: {:.3f}'.format(range), (int(ux + 4), int(uy - 4)), 0.4, CVColor.White, 1)
        # BaseDraw.draw_text(img, 'A: {:.2f}'.format(angle), (int(ux + 4), int(uy + 14)), 0.4, CVColor.White, 1)
        # BaseDraw.draw_text(img, 'Trange: {:.3f} angle:{:.2f}'.format(range, angle), (indent + 2, 140), 0.5,
        #                    CVColor.White, 1)

        self.show_text_info(target['source'], 160, 'range: {:.3f}'.format(range))
        self.show_text_info(target['source'], 180, 'angle: {:.2f}'.format(angle))
        self.show_text_info(target['source'], 200, 'Trange: {:.3f} angle:{:.2f}'.format(range, angle))
        return range, angle

    def show_rtk_target(self, img, target):
        indent = self.get_indent(target['source'])
        angle = target.get('angle')
        range = target.get('range')
        delta_h = target.get('delta_hgt')

        x, y = self.transform.trans_polar2rcs(angle, range, 'rtk')
        if x == 0:
            x = 0.001
        width = 0.5
        height = 0.5
        ux, uy = self.transform.trans_gnd2raw(x, y, delta_h + self.cfg.installs['rtk']['height'])
        w = self.cfg.installs['video']['fu'] * width / x
        w = max(10, min(50, w))
        h = w

        # p1 = int(ux - 0.5 * w), int(uy - 0.5 * h)
        # p2 = int(ux + 0.5 * w), int(uy + 0.5 * h)
        # p3 = int(ux + 0.5 * w), int(uy - 0.5 * h)
        # p4 = int(ux - 0.5 * w), int(uy + 0.5 * h)

        # cv2.line(img, p1, p2, color, 1)
        # cv2.line(img, p3, p4, color, 1)
        # cv2.line(img, p1, p3, color, 1)
        # cv2.line(img, p1, p4, color, 1)
        # cv2.line(img, p2, p3, color, 1)
        # cv2.line(img, p2, p4, color, 1)
        #
        # p5 = (int(ux + 80), int(uy - 0.5 * h - 80))
        # p6 = (p5[0] + 20, p5[1])
        #
        # cv2.line(img, (ux, uy), p5, color, 1)
        # cv2.line(img, p5, p6, color, 1)

        color = self.color_obs['rtk']
        p1 = int(ux - 0.5 * w), int(uy)
        p2 = int(ux + 0.5 * w), int(uy)
        p3 = int(ux), int(uy - 0.5 * h)
        p4 = int(ux), int(uy + 0.5 * h)

        cv2.line(img, p1, p2, color, 2)
        cv2.line(img, p3, p4, color, 2)

        if angle > 90 or angle < -90:
            BaseDraw.draw_text(img, 'RTK target on the back', (int(ux + 4), int(uy - 4)), 0.6, CVColor.White, 1)
            return
        # cv2.line(img, p1, p2, CVColor.Green if target['rtkst'] >= 48 else CVColor.Grey, 2)
        # cv2.line(img, p3, p4, CVColor.Green if host['rtkst'] >= 48 else CVColor.Grey, 2)


        # BaseDraw.draw_text(img, 'R: {:.2f}'.format(range), p5, 0.3, CVColor.White, 1)
        # BaseDraw.draw_text(img, 'A: {:.2f}'.format(angle), (p5[0], p5[1] - 10), 0.3, CVColor.White, 1)
        # BaseDraw.draw_text(img, 'Trange: {:.3f} angle:{:.2f}'.format(range, angle), (indent + 2, 140), 0.5,
        #                    CVColor.White, 1)
        self.show_text_info(target['source'], 160, 'range: {:.3f}'.format(range))
        self.show_text_info(target['source'], 180, 'angle: {:.2f}'.format(angle))
        self.show_text_info(target['source'], 200, 'TTC: {:.2f}'.format(target['TTC']))

    def show_ipm_target(self, img, target, host):
        range, angle = self._calc_relatives(target, host)
        x, y = self.transform.trans_polar2rcs(angle, range, 'rtk')
        ux, uy = self.transform.trans_gnd2ipm(x, y)
        color = CVColor.Green
        # if type == 0:
        #     color = CVColor.Green
        # elif type == 2:
        #     color = CVColor.Red

        w = h = 30

        p1 = int(ux - 0.5 * w), int(uy)
        p2 = int(ux + 0.5 * w), int(uy)
        p3 = int(ux), int(uy - 0.5 * h)
        p4 = int(ux), int(uy + 0.5 * h)

        cv2.line(img, p1, p2, color, 2)
        cv2.line(img, p3, p4, color, 2)

    def show_rtk_target_ipm(self, img, target):
        angle = target.get('angle')
        range = target.get('range')
        x, y = self.transform.trans_polar2rcs(angle, range, 'rtk')
        ux, uy = self.transform.trans_gnd2ipm(x, y)
        color = self.color_obs['rtk']

        w = h = 20

        p1 = int(ux - 0.5 * w), int(uy)
        p2 = int(ux + 0.5 * w), int(uy)
        p3 = int(ux), int(uy - 0.5 * h)
        p4 = int(ux), int(uy + 0.5 * h)

        cv2.line(img, p1, p2, color, 2)
        cv2.line(img, p3, p4, color, 2)

        BaseDraw.draw_text(img, '{:.2f}'.format(range), (int(ux + 4), int(uy + 20)), 0.3, color, 1)
        BaseDraw.draw_text(img, '{:.2f}'.format(angle), (int(ux + 4), int(uy + 10)), 0.3, color, 1)

    def show_mobile_parameters(self, img, parameters, point):
        """显示关键车参数信息
        Args:
            img: 原始图片
            parameters: List [type, index, ttc, fcw, hwm, hw, vb] 关键车参数
        """
        hwm = parameters[0]
        hw = parameters[1]
        fcw = parameters[2]
        vb = parameters[3]
        ldw = parameters[4]

        origin_x, origin_y = point
        gap_v = 20
        color = CVColor.Green
        BaseDraw.draw_text(img, 'fcw:' + fcw, (origin_x, origin_y + gap_v * 5), 0.5, color, 1)
        BaseDraw.draw_text(img, 'hwm:' + hwm, (origin_x, origin_y + gap_v * 6), 0.5, color, 1)
        BaseDraw.draw_text(img, 'hw:' + hw, (origin_x, origin_y + gap_v * 7), 0.5, color, 1)
        BaseDraw.draw_text(img, 'vb:' + vb, (origin_x, origin_y + gap_v * 8), 0.5, color, 1)
        BaseDraw.draw_text(img, 'ldw:' + ldw, (origin_x + 120 * 2, origin_y + gap_v * 4), 0.5, color, 1)

    def draw_corners(self, img):
        # 设置寻找亚像素角点的参数，采用的停止准则是最大循环次数30和最大误差容限0.001
        criteria = (cv2.TERM_CRITERIA_MAX_ITER | cv2.TERM_CRITERIA_EPS, 30, 0.001)
        # 转换成灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 角点检测 (9,6) 行角点个数9   列角点个数6
        ret, corners = cv2.findChessboardCorners(gray, (7, 7), None)
        # print(corners)
        if ret is not True:
            return
        # 亚像素精确定位角点位置
        corners2 = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), criteria)
        d1 = np.linalg.norm(corners2[0] - corners2[6])
        d2 = np.linalg.norm(corners2[6] - corners2[48])
        # print(d1, d2)
        # 图上绘制检测到的角点
        cv2.drawChessboardCorners(img, (7, 7), corners2, ret)

    def show_lane_ipm(self, img, data, color=CVColor.Cyan, style=""):
        """绘制车道线
        Args:
            img: 原始图片
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            width: float 车道线宽度
            color: CVColor 车道线颜色
        """
        # sensor = data['source'].split('.')[0]
        max_range = data['range']
        min_range = data.get("min_range", 0)
        ratios = (data['a0'], data['a1'], data['a2'], data['a3'])
        if max_range == 0:
            return
        p = self.transform.getp_ipm_from_poly(ratios, 1, min_range, max_range, sensor=data['source'])

        if style == "dotted":
            for i in range(2, len(p) - 1, 1):
                if i % 3 == 0:
                    BaseDraw.draw_line(img, p[i], p[i + 1], color, 2)
        else:
            for i in range(2, len(p) - 1, 1):
                BaseDraw.draw_line(img, p[i], p[i + 1], color, 2)

        # p = self.transform.getp_ipm_from_poly(ratios, 1, r, 160, param=install_para)
        #
        # for idx, i in enumerate(range(1, len(p) - 1, 1)):
        #     if idx % 2 == 0:
        #         BaseDraw.draw_line(img, p[i], p[i + 1], color, 1)

    def draw_vehicle_state(self, img, data):
        # indent = self.get_indent(data['source'])
        if len(data) == 0:
            return
        if 'speed' in data:
            self.show_veh_speed(img, data['speed'], data['source'])
        if 'TTC' in data:
            self.show_text_info(data['source'], 60, 'TTC: ' + '{:.2f}s'.format(data['TTC']))
        if 'pos_lon' in data and 'pos_lat' in data:
            dist = data.get('pos_lon') if 'pos_lon' in data else data['range']
            angle = data.get('angle') if 'angle' in data else atan2(data['pos_lat'], data['pos_lon']) * 180 / pi
            # BaseDraw.draw_text(img, 'range: {:.2f}'.format(dist), (indent + 2, line + 40), 0.5, CVColor.White, 1)
            self.show_text_info(data['source'], 80, 'R/A: {:.2f} / {:.2f}'.format(dist, angle))
        if 'yaw_rate' in data:
            self.show_yaw_rate(img, data['yaw_rate'], data['source'])

        if 'accel' in data:
            self.show_accel(img, data['accel'], data['source'])

    def cal_fps(self, frame_cnt):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        duration = duration if duration > 0 else 1
        fps = frame_cnt / duration
        return fps

    def show_intrinsic_para(self, img):
        indent = self.get_indent('video')
        BaseDraw.draw_text(img,
                           'Yaw  Pitch  Roll',
                           (1180, 700), 0.3, CVColor.White, 1)
        BaseDraw.draw_text(img,
                           '{:.2f} {:.2f}  {:.2f}'.format(self.cfg.installs['video']['yaw'],
                                                          self.cfg.installs['video']['pitch'],
                                                          self.cfg.installs['video']['roll']),
                           (1180, 710), 0.3, CVColor.White, 1)

    def show_failure(self, img, failure):
        y = int(img.shape[0]/2)
        BaseDraw.draw_text(img, failure, (100, y), 2, CVColor.Red, 2)

    def show_warning_ifc(self, img, title):
        # print(title)
        if isinstance(title, list):
            for idx, t in enumerate(title):
                # print(idx)
                BaseDraw.draw_text(img, t, (10, 200 + idx * 80), 2, CVColor.Red, 3)
        else:
            BaseDraw.draw_text(img, title, (10, 200), 2, CVColor.Red, 3)

    def show_ub482_common(self, img, data):
        indent = self.get_indent(data['source'])
        # return
        # print(data['type'], data['ts'], data['sol_stat'], data['pos_type'])
        # self.update_column_ts(data['source'], data['ts'])
        color = CVColor.White
        style_list = {'NONE': 'fail', 'DOPPLER_VELOCITY': 'pass', 'NARROW_INT': 'pass',
                      'INS_RTKFIXED': 'pass', 'INS_PSRSP': 'pass'}
        if data['type'] == 'bestpos':
            # BaseDraw.draw_text(img, '{}'.format(data['pos_type']), (indent + 142, 40), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'lat: {:.8f}'.format(data['lat']), (indent + 142, 60), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'lon:{:.8f}'.format(data['lon']), (indent + 142, 80), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'hgt: {:.3f}'.format(data['hgt']), (indent + 142, 100), 0.5, color, 1)
            self.show_text_info(data['source'], 40, 'P:{}'.format(data['pos_type']), style_list.get(data['pos_type']))
            self.show_text_info(data['source'], 80, 'lat: {:.8f}'.format(data['lat']))
            self.show_text_info(data['source'], 100, 'lon:{:.8f}'.format(data['lon']))
            self.show_text_info(data['source'], 120, 'hgt: {:.3f}'.format(data['hgt']))
            self.show_text_info(data['source'], 60, '#SVs/sol: {}/{}'.format(data['#SVs'], data['#solSVs']))

        if data['type'] == 'inspva':
            self.show_text_info(data['source'], 40, 'P:{}'.format(data['pos_type']), style_list.get(data['pos_type']))
            self.show_text_info(data['source'], 80, 'lat: {:.8f}'.format(data['lat']))
            self.show_text_info(data['source'], 100, 'lon:{:.8f}'.format(data['lon']))
            self.show_text_info(data['source'], 120, 'hgt: {:.3f}'.format(data['hgt']))
        if data['type'] == 'heading':
            # BaseDraw.draw_text(img, '{}'.format(data['pos_type']), (indent + 2, 40), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'yaw: {:.2f}'.format(data['yaw']), (indent + 2, 60), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'pitch: {:.2f}'.format(data['pitch']), (indent + 2, 80), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'len: {:.3f}'.format(data['length']), (indent + 2, 100), 0.5, color, 1)
            self.show_text_info(data['source'], 140, 'H:{}'.format(data['pos_type']), style_list.get(data['pos_type']))
            self.show_text_info(data['source'], 180, 'Yaw  Pitch Len '.format(data['yaw']))
            self.show_text_info(data['source'], 200,
                                '{:.2f} {:.2f} {:.2f}'.format(data['yaw'], data['pitch'], data['length']))
            self.show_text_info(data['source'], 160, '#SVs/sol: {}/{}'.format(data['#SVs'], data['#solSVs']))
            # self.show_text_info(data['source'], 180, 'len: {:.3f}'.format(data['length']))
        if data['type'] == 'bestvel':
            # BaseDraw.draw_text(img, 'V:{}'.format(data['pos_type']), (indent + 2, 120), 0.5, color, 1)
            self.show_text_info(data['source'], 220, 'V:{}'.format(data['pos_type']), style_list.get(data['pos_type']))

        if data['type'] == 'rtcm':
            BaseDraw.draw_text(img, 'rtcm rcv:{}'.format(data['len']), (indent + 82, 20), 0.5, color, 1)

    def show_rtk_pva(self, img, data):
        style_list = {'NONE': 'fail', 'DOPPLER_VELOCITY': 'pass', 'NARROW_INT': 'pass', 'INS_RTKFIXED': 'pass'}

        for key in data:
            if key == 'pos_type':
                self.show_text_info(data['source'], 40, 'P:{}'.format(data['pos_type']),
                                    style_list.get(data['pos_type']))
            elif key == 'lat':
                self.show_text_info(data['source'], 80, 'lat: {:.8f}'.format(data['lat']))
            elif key == 'lon':
                self.show_text_info(data['source'], 100, 'lon:{:.8f}'.format(data['lon']))
            elif key == 'hgt':
                self.show_text_info(data['source'], 120, 'hgt: {:.3f}'.format(data['hgt']))
        if '#SVs' in data and '#solSVs' in data:
            self.show_text_info(data['source'], 160, '#SVs/sol: {}/{}'.format(data['#SVs'], data['#solSVs']))
        if 'pitch' in data and 'yaw' in data:
            if 'roll' in data:
                self.show_text_info(data['source'], 180, 'Yaw  Pitch Roll ')
                self.show_text_info(data['source'], 200,
                                    '{:.2f} {:.2f} {:.2f}'.format(data['yaw'], data['pitch'], data['roll']))
            elif 'length' in data:
                self.show_text_info(data['source'], 180, 'Yaw  Pitch Len ')
                self.show_text_info(data['source'], 200,
                                    '{:.2f} {:.2f} {:.2f}'.format(data['yaw'], data['pitch'], data['length']))

        self.update_column_ts(data['source'], data['ts'])

    def show_gps(self, data):
        # if 'pos_type' in data:
        #     self.show_text_info(data['source'], 20, 'ptype:{}'.format(data['pos_type']))
        if 'speed' in data:
            self.show_text_info(data['source'], 40, '{:.1f} km/h'.format(data['speed']))
        if 'lat' in data:
            # BaseDraw.draw_text(img, 'lat:{:.5f}'.format(data['lat']), (indent + 2, 60), 0.5, CVColor.White, 1)
            self.show_text_info(data['source'], 60, 'lat:{:.5f}'.format(data['lat']))
        if 'lon' in data:
            # BaseDraw.draw_text(img, 'lon:{:.5f}'.format(data['lon']), (indent + 2, 80), 0.5, CVColor.White, 1)
            self.show_text_info(data['source'], 80, 'lon:{:.5f}'.format(data['lon']))
        if 'ts_origin' in data or 'ts' in data:
            ts = data.get('ts_origin') or data['ts']
            ta = time.localtime(ts)
            FORMAT = '%Y/%m/%d'
            date = time.strftime(FORMAT, ta)
            FORMAT = '%H:%M:%S'
            time_ = time.strftime(FORMAT, ta)
            # BaseDraw.draw_text(img, '{}'.format(date), (indent + 2, 100), 0.5, CVColor.White, 1)
            # BaseDraw.draw_text(img, '{}'.format(time_), (indent + 2, 120), 0.5, CVColor.White, 1)
            self.show_text_info(data['source'], 100, '{}'.format(date))
            self.show_text_info(data['source'], 120, '{}'.format(time_))

    def show_rtcm(self, data):
        if 'lat' in data:
            # BaseDraw.draw_text(img, 'lat:{:.5f}'.format(data['lat']), (indent + 2, 60), 0.5, CVColor.White, 1)
            self.show_text_info(data['source'], 60, 'lat:{:.5f}'.format(data['lat']))
        if 'lon' in data:
            # BaseDraw.draw_text(img, 'lon:{:.5f}'.format(data['lon']), (indent + 2, 80), 0.5, CVColor.White, 1)
            self.show_text_info(data['source'], 80, 'lon:{:.5f}'.format(data['lon']))

    def _calc_relatives(self, target, host):
        range = gps_distance(target['lat'], target['lon'], host['lat'], host['lon'])
        angle = gps_bearing(target['lat'], target['lon'], host['lat'], host['lon'])
        angle = angle - host['yaw']
        return range, angle

    def get_alert(self, vehicle_data, lane_data, ped_data):
        alert = {}
        warning_level, alert_ttc, hw_state, fcw_state, vb_state, sg_state = 0, 0, 0, 0, 0, 0
        if vehicle_data:
            speed = vehicle_data['speed']
            focus_index = vehicle_data['focus_index']
            if focus_index != -1:
                fcw_state = vehicle_data['forward_collision_warning']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                vb_state = vehicle_data['bumper_state']
                sg_state = vehicle_data['stop_and_go_state']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                warning_level = vehicle_data['warning_level']
                hw_state = vehicle_data['headway_warning']
        alert['ttc'] = float(alert_ttc)
        alert['warning_level'] = int(warning_level)
        alert['hw_state'] = int(hw_state)
        alert['fcw_state'] = int(fcw_state)
        alert['vb_state'] = int(vb_state)
        alert['sg_state'] = int(sg_state)

        lane_warning = 0
        speed = 0
        if lane_data:
            lane_warning = lane_data['deviate_state']
            speed = lane_data['speed'] * 3.6
        alert['lane_warning'] = lane_warning
        alert['speed'] = float('%.2f' % speed)

        return alert

    def draw_lane_r(self, img, data):
        if len(data) == 0:
            return
            # print(data)
        if data['type'] != 'lane':
            return

        # if 'color' in data:
        #     color = self.color_seq[data['color']]
        # else:
        #     color = CVColor.Blue
        color = self.color_obs.get(data['source'].split('.')[0])
        if not color:
            color = self.color_obs['default']
        # self.show_lane(img, (data['a0'], data['a1'], data['a2'], data['a3']), data['range'], color=color)
        # lane message
        self.show_lane(img, data, color=color, style=data.get("style"))

    def draw_lane_ipm(self, img, data):
        if len(data) == 0:
            return
        if data['type'] != 'lane':
            return

        # if 'color' in data:
        #     color = self.color_seq[data['color']]
        # else:
        #     color = CVColor.Blue
        color = self.color_obs.get(data['source'].split('.')[0])
        if not color:
            color = self.color_obs['default']

        self.show_lane_ipm(img, data, color, style=data.get("style"))

    def show_host_path(self, img, spd, yr, yrbias=0.0017, cipv_dist=200.0):
        # if spd < 5:
        #     return
        spd = spd / 3.6

        p1 = []
        p2 = []
        R = 1000
        x0 = -1.2
        yr = yr - yrbias
        if yr > 0.00001 or yr < -0.00001:
            R = spd / yr
        # print('R:', R)

        for x in range(0, min(int(abs(R)), int(spd * 6), cipv_dist), 5):
            # for x in range(0, 80):
            if yr < 0.0:
                y = (abs(R ** 2 - (x - x0) ** 2)) ** 0.5 + R
            elif yr > 0.0:
                y = -(abs(R ** 2 - (x - x0) ** 2)) ** 0.5 + R
            else:
                y = 0
            y1 = y - 0.9
            y2 = y + 0.9
            p1.append(self.transform.trans_gnd2raw(x, y1))
            p2.append(self.transform.trans_gnd2raw(x, y2))

        for i in range(0, len(p1) - 1, 1):
            # BaseDraw.draw_line(img, p1[i], p1[i + 1], CVColor.Grass, 2)
            # BaseDraw.draw_line(img, p2[i], p2[i + 1], CVColor.Grass, 2)
            # alpha = (1 - i / len(p1)) * 0.4
            BaseDraw.draw_alpha_poly(img, np.array([p1[i], p1[i + 1], p2[i + 1], p2[i]]), 0.2, FlatColor.emerald)

            # if i % 20 == 0 or i == 10:
            #     BaseDraw.draw_line(img, p1[i], p2[i], CVColor.Grass, 2)
            #     BaseDraw.draw_text(img, '{}m'.format(i), (p1[i][0], p1[i][1] + 10), 0.5, CVColor.Green, 1)
            # x, y, w, h = 200, 360, 880, 360
            # pt0 = (p1[i][0] - x, p1[i][1]-y)
            # pt1 = (p1[i+1][0] - x, p1[i+1][1] - y)
            # pt2 = (p2[i+1][0] - x, p2[i+1][1] - y)
            # pt3 = (p2[i][0] - x, p2[i][1] - y)
            # roi = img[360:720, 200:1080]
            # img1 = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
            # vtxs = np.array([[p1[i], p1[i+1], p2[i+1], p2[i]]])
            # vtxs = np.array([[pt0, pt1, pt2, pt3]])
            # BaseDraw.draw_alpha_rect(img, (p1[i][0], p1[i][1], abs(p2[i][0] - p1[i][0]), abs(p2[i][1] - p1[i][1])), 0.4)
            # cv2.fillPoly(img, vtxs, (0, 200, 0))
            # cv2.addWeighted(img, 0.9, img1, 0.2, 0, img1)

    def show_host_path_ipm(self, img, spd, yr, yrbias=0.0017):
        # if spd < 5:
        #     return
        spd = spd / 3.6
        veh_w = 1.86

        p1 = []
        p2 = []
        R = 1000
        R1 = 1000
        R2 = 1000
        x0 = -1.2
        yr = yr - yrbias
        if yr > 0.00001 or yr < -0.00001:
            R = spd / yr
            if R > 0:
                R1 = R - veh_w / 2
                R2 = R + veh_w / 2
                # print(R1)

            else:
                R1 = R + veh_w / 2
                R2 = R - veh_w / 2

        # print('R:', R)

        for x in range(0, min(int(abs(R)), int(spd * 6)), 5):
            if yr < 0.0:
                # R1 = R - 0.9
                # R2 = R + 0.9
                y = (abs(R1 ** 2 - (x - x0) ** 2)) ** 0.5 + R1
                # y1 = (abs(R1 ** 2 - (x - x0) ** 2)) ** 0.5 + R1
                # y2 = (abs(R2 ** 2 - (x - x0) ** 2)) ** 0.5 + R2
            elif yr > 0.0:
                # R1 = R + 0.9
                # R2 = R - 0.9
                y = -(abs(R1 ** 2 - (x - x0) ** 2)) ** 0.5 + R1
                # y1 = -(abs(R1 ** 2 - (x - x0) ** 2)) ** 0.5 + R1
                # y2 = -(abs(R2 ** 2 - (x - x0) ** 2)) ** 0.5 + R2
            else:
                y = 0
                # y1 = 0
                # y2 = 0
            y1 = y - 1
            y2 = y + 1
            p1.append(self.transform.trans_gnd2ipm(x, y1))
            p2.append(self.transform.trans_gnd2ipm(x, y2))

        for i in range(0, len(p1) - 1, 1):
            # BaseDraw.draw_line(img, p1[i], p1[i + 1], CVColor.Green, 1)
            # BaseDraw.draw_line(img, p2[i], p2[i + 1], CVColor.Green, 1)
            alpha = (1 - i / len(p1)) * 0.4
            BaseDraw.draw_alpha_poly(img, np.array([p1[i], p1[i + 1], p2[i + 1], p2[i]]), alpha, FlatColor.emerald)
            # cv2.fillConvexPoly(img, np.array([p1[i], p1[i+1], p2[i+1], p2[i]]), CVColor.Green)
