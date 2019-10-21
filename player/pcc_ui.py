from player.ui import BaseDraw, pack, logodir, CVColor
from config.config import install
import cv2
from tools.transform import Transform
from datetime import datetime
import time
from tools.geo import gps_bearing, gps_distance
import numpy as np
import logging

# logging.basicConfig函数对日志的输出格式及方式做相关配置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class InfoCard(object):
    pos_x = 0
    pos_y = 0
    width = 0
    height = 0
    buffer = {}
    ts = 0


class Player(object):
    """图片播放器"""
    def __init__(self):
        self.overlook_background_image = cv2.imread(pack(logodir, 'back.png'))
        self.circlesmall_image = cv2.imread(pack(logodir, 'circlesmall.tif'))
        self.sectorwide_image = cv2.imread(pack(logodir, 'sectorwide.tif'))
        self.sectorthin_image = cv2.imread(pack(logodir, 'sectorthin.tif'))
        self.car_image = cv2.imread(pack(logodir, 'car.tif'))
        self.overlook_othercar_image = cv2.imread(pack(logodir, 'othercar.tif'))
        self.overlook_beforecar_image = cv2.imread(pack(logodir, 'before.tif'))
        self.transform = Transform()

        self.indent = 160
        self.columns = {'video': {'indent': 0, 'buffer': {}, 'ts': 0}}
        self.param_bg_width = 160
        self.ts_now = 0
        self.rtk = {}

        self.start_time = datetime.now()
        self.cipv = 0

        self.color_seq = [CVColor.White, CVColor.Red, CVColor.Green, CVColor.deeporange, CVColor.purple,
             CVColor.Blue, CVColor.LightBlue, CVColor.Black, CVColor.Grass]

        self.color_obs = {'ifv300': CVColor.Blue,
             'esr': CVColor.Red,
             'lmr': CVColor.Green,
             'x1': CVColor.purple,
             'rtk': CVColor.Green,
             'ars': CVColor.Green,
             'gps': 0,
             'sta77': CVColor.Black,
             'mbq4': CVColor.Grass}

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
            self.columns[msg_type] = {'indent': self.indent}
            # if 'rtk' in msg_type:
            #     self.indent += 300
            # else:
            self.indent += 160
            for src_type in self.color_obs:
                if msg_type.split('.')[0] in src_type:
                    self.columns[msg_type]['color'] = self.color_obs[src_type]
            self.columns[msg_type]['buffer'] = dict()
            self.columns[msg_type]['ts'] = 0
        self.param_bg_width = self.indent + 20

    def get_indent(self, source):
        if source in self.columns:
            return self.columns[source]['indent']
        else:
            self.add_info_column(source)
            return self.columns[source]['indent']

    def show_dist_mark_ipm(self, img):
        for i in range(5, 200, 1):
            if i % 20 == 0 or i == 10:
                p1 = self.transform.trans_gnd2ipm(i, -10)
                p2 = self.transform.trans_gnd2ipm(i, 10)
                BaseDraw.draw_line(img, p1, p2, color_type=CVColor.Midgrey, thickness=1)
                BaseDraw.draw_text(img, '{}m'.format(i), p2, 0.3, CVColor.White, 1)

        for i in range(-10, 11, 5):
            p1 = self.transform.trans_gnd2ipm(-10, i)
            p2 = self.transform.trans_gnd2ipm(170, i)
            BaseDraw.draw_line(img, p1, p2, color_type=CVColor.Midgrey, thickness=1)
            BaseDraw.draw_text(img, '{}m'.format(i), p2, 0.3, CVColor.White, 1)

    # def show_overlook_background(self, img):
    #     """绘制俯视图的背景，包括背景图，车背景图，光线图
    #     Args:
    #         img: 原始图片
    #     """
    #     y_background, x_background, _ = self.overlook_background_image.shape
    #     y_img, x_img, _ = img.shape
    #     roi_img = img[0: y_background, x_img - x_background: x_img]
    #     cv2.addWeighted(self.overlook_background_image, 1, roi_img, 0.4, 0.0, roi_img)
    #     x_center, y_center = 1144, 240
    #
    #     data_r = int(1) % 20 + 120
    #
    #     draw_r = []
    #     while data_r > 30:
    #         draw_r.append(data_r)
    #         data_r = data_r - 20
    #     draw_r.append(140)
    #
    #     y_circle, x_circle, _ = self.circlesmall_image.shape
    #     for R in draw_r:
    #         x_new, y_new = int(R), int(y_circle * R / x_circle)
    #         new_circle = cv2.resize(self.circlesmall_image, (y_new, x_new),
    #                                 interpolation=cv2.INTER_CUBIC)
    #         x_begin = x_center - x_new // 2
    #         x_end = x_begin + x_new
    #         y_begin = y_center - y_new // 2
    #         y_end = y_begin + y_new
    #         roi_img = img[y_begin: y_end, x_begin: x_end]
    #         cv2.addWeighted(new_circle, 0.5, roi_img, 1.0, 0.0, roi_img)
    #
    #     for sector_in in [self.sectorwide_image, self.sectorthin_image]:
    #         y_sector, x_sector, _ = sector_in.shape
    #         x_begin = 1145 - x_sector // 2
    #         x_end = x_begin + x_sector
    #         y_end = 219
    #         y_begin = y_end - y_sector
    #         roi_img = img[y_begin: y_end, x_begin: x_end]
    #         cv2.addWeighted(sector_in, 0.5, roi_img, 1.0, 0.0, roi_img)
    #
    #     y_car, x_car, _ = self.car_image.shape
    #     x_begin = x_center - x_car // 2 - 3
    #     x_end = x_begin + x_car
    #     y_begin = y_center - y_car // 2
    #     y_end = y_begin + y_car
    #     roi_img = img[y_begin: y_end, x_begin: x_end]
    #     cv2.addWeighted(self.car_image, 1.0,
    #                     roi_img, 1.0, 0.0, roi_img)

    def show_parameters_background(self, img, rect):
        """左上角参数背景图"""
        BaseDraw.draw_alpha_rect(img, rect, 0.4)

    def show_columns(self, img):
        w = self.param_bg_width
        # self.show_parameters_background(img, (0, 0, w if w <= 1280 else 1280, 150))
        for col in self.columns:
            indent = self.columns[col]['indent']
            x0 = indent
            y0 = 0
            x1 = indent + 140
            y1 = max(self.columns[col]['buffer']) if self.columns[col]['buffer'] else 0
            self.show_parameters_background(img, (x0, y0, x1 if x1 <= 1280 else 1280, y1))

            BaseDraw.draw_text(img, col, (indent + 12, 20), 0.5, CVColor.Cyan, 1)
            if col is not 'video':
                cv2.rectangle(img, (indent, 0), (indent + 140, 20), self.columns[col]['color'], -1)

    def show_obs(self, img, obs, thickness=2):
        try:
            indent = self.get_indent(obs['source'])
        except Exception as e:
            print('Error indent', obs)
        color = obs.get('color')
        if color:
            color = self.color_seq[color]
        else:
            color = self.color_seq[0]

        width = obs.get('width')
        width = width or 0.3
        height = obs.get('height')
        # print(obs['source'], obs['class'])
        height = height or width
        if obs.get('class') == 'pedestrian' or obs.get('class') == 'PEDESTRIAN':
            height = 1.7
        if 'pos_lon' in obs:
            x = obs['pos_lon']
            y = obs['pos_lat']
        else:
            # print(obs['source'].split('.')[0])
            # x, y = self.transform.trans_polar2rcs(obs['angle'], obs['range'], install[obs['source'].split('.')[0]])
            install_para = install[obs['source'].split('.')[0]]
            if install_para is None:
                x, y = self.transform.trans_polar2rcs(obs['angle'], obs['range'])
            else:
                x, y = self.transform.trans_polar2rcs(obs['angle'], obs['range'], install_para)
        if x == 0:
            x = 0.1
        if x < 0:
            return

        w = install['video']['fv'] * width / x
        if w > 600:
            w = 600
        dev = obs.get('source')
        if dev:
            dev = dev.split('.')[0]
            # print(dev)
        else:
            dev = 'default'
        x0, y0 = self.transform.trans_gnd2raw(x, y, dev=dev)

        h = w
        h = 1200 * height / x
        x1 = x0 - 0.5 * w
        y1 = y0 - h
        x2 = x1 + w
        y2 = y1 + h
        x1 = int(x1)
        x2 = int(x2)
        y1 = int(y1)
        y2 = int(y2)
        if obs.get('sensor_type') == 'radar':
            if w > 50:
                w = 50
            # print(int(x1), int(y1), int(w), width)
            cv2.circle(img, (int(x0), int(y0-0.5*h)), int(w), color, 1)
            BaseDraw.draw_text(img, '{}'.format(obs['id']), (x1 + int(1.4 * w), y1 + int(1.4 * w)), 0.45, color, 1)
        elif obs.get('class') == 'pedestrian':
            # print(obs)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
            BaseDraw.draw_text(img, '{}'.format(obs['id']), (x1 - 2, y1 - 4), 0.45, color, 1)
        else:
            BaseDraw.draw_rect_corn(img, (x1, y1), (x2, y2), color, thickness)
            BaseDraw.draw_text(img, '{}'.format(obs['id']), (x1 - 2, y1 - 4), 0.45, color, 1)

        if 'cipo' in obs and obs['cipo']:
            # color = CVColor.Yellow
            self.show_cipo_info(img, obs)
            BaseDraw.draw_up_arrow(img, x0, y0 + 3, color)

        # if 'TTC' in obs:
        #     self.show_ttc(img, obs['TTC'], obs['source'])

    def show_ipm_obs(self, img, obs):
        id = obs['id']
        if 'pos_lon' in obs:
            x = obs['pos_lon']
            y = obs['pos_lat']
        else:
            x, y = self.transform.trans_polar2rcs(obs['angle'], obs['range'], install[obs['source'].split('.')[0]])
        u, v = self.transform.trans_gnd2ipm(x, y)

        color = self.color_seq[obs['color']]

        if obs.get('sensor_type') == 'radar':
            cv2.circle(img, (u, v-8), 8, color, 2)
            BaseDraw.draw_text(img, '{}'.format(id), (u - 28, v - 8), 0.4, color, 1)
            # ESR
            if 'TTC' in obs:
                # for save space, only ttc<7 will be shown on the gui
                if obs['TTC'] < 7:
                    BaseDraw.draw_text(img, '{:.2f}'.format(obs['TTC']), (u - 40, v + 5), 0.4, color, 1)

            # STA 77
            if obs.get('sensor') == 'sta77':
                BaseDraw.draw_text(img, '{:.1f}'.format(x), (u - 40, v + 5), 0.4, color, 1)

        else:
            if obs.get('class') == 'pedestrian' or obs.get('class') == 'PEDESTRIAN':
                cv2.rectangle(img, (u - 4, v - 16), (u + 4, v), color, 2)
            else:
                cv2.rectangle(img, (u - 8, v - 16), (u + 8, v), color, 2)
            BaseDraw.draw_text(img, '{}'.format(id), (u + 10, v - 8), 0.4, color, 1)
            BaseDraw.draw_text(img,  '{:.1f}'.format(x), (u + 10, v +5), 0.4, color, 1)

    def show_lane(self, img, data, ratios, r=60, color=CVColor.Cyan):
        """绘制车道线
        Args:
            img: 原始图片
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            width: float 车道线宽度
            color: CVColor 车道线颜色
        """
        p = self.transform.getp_ifc_from_poly(ratios, r, 1)

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
                BaseDraw.draw_text(img, 'class: ' + data['type_class'], (tx-50, ty), 0.5, color, 1)

            if 'prediction_source' in data:
                BaseDraw.draw_text(img, 'predict: ' + data['prediction_source'], (tx-50, ty+text_step), 0.5, color, 1)

            if 'probability' in data:
                BaseDraw.draw_text(img, 'prob: ' + str('%.2f' % data['probability']), (tx-50, ty+text_step*2), 0.5, color, 1)

    # def show_tsr(self, img, position, color=CVColor.Cyan, thickness=2):
    #     """绘制tsr框
    #     Args:
    #         img: 原始图片
    #         position: (x, y, width, height),框的位置，大小
    #         color: CVColor 颜色
    #         thickness: int 线粗
    #     """
    #
    #     x, y, width, height = position
    #     x1 = int(x)
    #     y1 = int(y)
    #     width = int(width)
    #     height = int(height)
    #     x2 = x1 + width
    #     y2 = y1 + height
    #     BaseDraw.draw_rect(img, (x1, y1), (x2, y2), color, thickness)

    # def show_tsr_info(self, img, position, max_speed):
    #     """绘制车辆信息
    #     Args:
    #         img: 原始图片
    #         position: (x, y, width, height),车辆框的位置，大小
    #         max_speed: float
    #     """
    #     x, y, width, height = position
    #     x1 = int(x)
    #     y1 = int(y)
    #     width = int(width)
    #     height = int(height)
    #     x2 = x1 + width
    #     y2 = y1 + height
    #     origin_x = max(0, x2 - 40)
    #     origin_y = max(0, y2)
    #     BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 40, 20), 0.6)
    #     BaseDraw.draw_text(img, str(max_speed), (x2 - 30, y2 + 5),
    #                        1, CVColor.Green, 1)

    # def show_tsr_parameters(self, img, parameters, point):
    #     """显示tsr信息
    #     Args:
    #         img: 原始图片
    #         parameters: List [index, TODO ]
    #     """
    #     index = parameters[0]
    #     speed_limit = parameters[1]
    #     warning_level = parameters[2]
    #     warning_state = parameters[3]
    #
    #     origin_x, origin_y = point
    #     gap_v = 20
    #     size = 0.5
    #     BaseDraw.draw_text(img, 'tsr', (origin_x, origin_y + gap_v), size, CVColor.Cyan, 1)
    #     BaseDraw.draw_text(img, 'focus_index:' + index, (origin_x, origin_y + gap_v * 2), size, CVColor.White, 1)
    #     BaseDraw.draw_text(img, 'speed_limit:' + speed_limit, (origin_x, origin_y + gap_v * 3), size, CVColor.White, 1)
    #     BaseDraw.draw_text(img, 'warning_level:' + warning_level, (origin_x, origin_y + gap_v * 4), size, CVColor.White,
    #                        1)
    #     BaseDraw.draw_text(img, 'warning_state:' + warning_state, (origin_x, origin_y + gap_v * 5), size, CVColor.White,
    #                        1)

    # def show_env(self, img, speed, light_mode, fps, point):
    #     """显示环境信息
    #     Args:
    #         img: 原始图片
    #         light_mode: 白天或夜间
    #         fps: 帧率
    #     """
    #     origin_x, origin_y = point
    #     origin_x += 10
    #     BaseDraw.draw_text(img, 'env', (origin_x, origin_y + 20), 0.5, CVColor.Cyan, 1)
    #     BaseDraw.draw_text(img, 'light:' + str(light_mode), (origin_x, origin_y + 40), 0.5, CVColor.White, 1)
    #     BaseDraw.draw_text(img, 'speed:' + str(int(speed)), (origin_x, origin_y + 60), 0.5, CVColor.White, 1)
    #     BaseDraw.draw_text(img, 'fps:' + str(int(fps)), (origin_x, origin_y + 80), 0.5, CVColor.White, 1)
    def show_text_info(self, source, height, text, style='normal'):
        if style is None:
            style = 'warning'
        self.get_indent(source)
        self.columns[source]['buffer'][height] = {'text': text, 'style': style}
        # print(source, height, text)

    def update_column_ts(self, source, ts):
        if not source:
            return
        self.columns[source]['ts'] = ts

    def render_text_info(self, img):
        # self.show_columns(img)
        # print(len(self.columns))
        for col in self.columns:
            entry = self.columns[col]
            indent = self.columns[col]['indent']
            x0 = indent
            y0 = 0
            w = 160
            h = max(self.columns[col]['buffer']) + 2 if self.columns[col]['buffer'] else 20
            h = 20 if h == 0 else h

            if col is not 'video':
                color_lg = self.columns[col].get('color')
                if color_lg is not None:
                    cv2.rectangle(img, (indent+1, 1), (indent + 159, 24), self.columns[col]['color'], -1)
            self.show_parameters_background(img, (x0, y0, w if w <= 1280 else 1280, h))
            BaseDraw.draw_text(img, col, (indent+2, 20), 0.5, CVColor.Cyan, 1)
            dt = self.ts_now-self.columns[col]['ts']

            BaseDraw.draw_text(img, '{:>+4d}ms'.format(int(dt*1000)), (indent + 92, 20), 0.5, CVColor.White, 1)
            # if col is not 'video':
            #     cv2.rectangle(img, (indent, 0), (indent + 160, 20), self.columns[col]['color'], -1)
            for height in entry['buffer']:
                # print(col, height, entry['buffer'])
                style = entry['buffer'][height]['style']
                style_list = {'normal': None, 'warning': CVColor.Yellow, 'fail': CVColor.Red, 'pass': CVColor.Green}
                if style_list.get(style):
                    color = style_list.get(style)
                else:
                    color = CVColor.White
                line_len = len(entry['buffer'][height]['text'])
                size = min(0.5 * 16 / line_len, 0.5)
                size = max(0.24, size)
                BaseDraw.draw_text(img, entry['buffer'][height]['text'], (entry['indent'] + 2, height), size, color, 1)

    def show_video_info(self, img, data):
        self.show_parameters_background(img, (0, 0, 40, 20))
        BaseDraw.draw_text(img, data['source'], (2, 20), 0.5, CVColor.Cyan, 1)

    def show_frame_id(self, img, source, fn):
        # indent = self.columns['video']['indent']
        # BaseDraw.draw_text(img, 'fid: ' + str(int(fn)), (indent + 2, 40), 0.5, CVColor.White, 1)
        self.show_text_info(source, 40, 'frame: ' + str(int(fn)))

    def show_pinpoint(self, img, pp):
        BaseDraw.draw_text(img, 'Pin: {lat:.8f} {lon:.8f} {hgt:.3f}'.format(**pp), (950, 710), 0.3, CVColor.White, 1)

    def show_frame_cost(self, cost):
        self.show_text_info('video', 80, 'render_cost: {}ms'.format(int(cost*1000)))

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
        yr_deg = yr*57.3
        # BaseDraw.draw_text(img, '%.1f' % yr_deg + ' deg/s', (indent + 2, 60), 0.5, CVColor.White, 1)
        self.show_text_info(source, 60, '{:.1f}deg/s'.format(yr_deg))

    def show_q3_veh(self, img, speed, yr):
        BaseDraw.draw_text(img, 'q3spd: ' + str(int(speed * 3.6)), (2, 120), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'q3yr: ' + '%.4f' % yr, (2, 140), 0.5, CVColor.White, 1)
        # self.show_text_info(source, 40, )
    def show_recording(self, img, info):
        time_passed = time.time() - info
        BaseDraw.draw_text(img, 'Recording... ', (2, 700), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'time elapsed: {:.2f}s'.format(time_passed), (2, 712), 0.5, CVColor.White, 1)

    def show_replaying(self, img, dts):
        time_passed = dts
        BaseDraw.draw_text(img, 'Replaying... ', (2, 700), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'time elapsed: {:.2f}s'.format(time_passed), (2, 712), 0.5, CVColor.White, 1)

    def show_cipo_info(self, img, obs):
        try:
            indent = self.get_indent(obs['source'])
        except Exception as e:
            print('Error:', obs)
            return
        if obs.get('class') == 'pedestrian':
            line = 40
            # BaseDraw.draw_text(img, 'CIPPed: {}'.format(obs['id']), (indent + 18, line), 0.5, CVColor.White, 1)
            self.show_text_info(obs['source'], line, 'CIPPed: {}'.format(obs['id']))
        elif obs.get('class') == 'object':
            line = 100
            # BaseDraw.draw_text(img, 'CIPO: {}'.format(obs['id']), (indent + 18, line), 0.5, CVColor.White, 1)
            self.show_text_info(obs['source'], line, 'CIPO: {}'.format(obs['id']))
        else:
            line = 100
            # BaseDraw.draw_text(img, 'CIPVeh: {}'.format(obs['id']), (indent + 18, line), 0.5, CVColor.White, 1)
            self.show_text_info(obs['source'], line, 'CIPVeh: {}'.format(obs['id']))

        if 'TTC' in obs:
            # BaseDraw.draw_text(img, 'TTC: ' + '{:.2f}s'.format(obs['TTC']), (indent + 2, line + 20), 0.5, CVColor.White,
            #                    1)
            self.show_text_info(obs['source'], line+20, 'TTC: ' + '{:.2f}s'.format(obs['TTC']))
        dist = obs.get('pos_lon') if 'pos_lon' in obs else obs['range']
        # BaseDraw.draw_text(img, 'range: {:.2f}'.format(dist), (indent + 2, line + 40), 0.5, CVColor.White, 1)
        self.show_text_info(obs['source'], line + 40, 'range: {:.2f}'.format(dist))
        BaseDraw.draw_up_arrow(img, indent + 100, line - 12, self.color_seq[obs['color']], 6)

    def _show_rtk(self, img, rtk):
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
        BaseDraw.draw_text(img, 'delay: {:.4f}'.format(rtk['ts']-rtk['ts_origin']), (indent + 2, 120), 0.5, color, 1)
        vel = (rtk['velN'] ** 2 + rtk['velE'] ** 2) ** 0.5
        BaseDraw.draw_text(img, '{:.2f}km/h'.format(vel*3.6), (indent + 142, 120), 0.5, color, 1)
        if 'sat' in rtk:
            BaseDraw.draw_text(img, '#rtk:{}/{} #ori:{}/{}'.format(rtk['sat'][1], rtk['sat'][0], rtk['sat'][5], rtk['sat'][4]), (indent + 50, 20), 0.5, color, 1)

    def show_rtk(self, img, rtk=None):
        if not rtk or rtk.get('rtkst') is None:
            for s in self.rtk:
                d = self.rtk[s]
                dt = self.ts_now - d['ts']
                # print(self.ts_now)
                if dt > 0.25:
                    d['updated'] = False
                self._show_rtk(img, d)
            return

        self._show_rtk(img, rtk)
        # rtk['updated'] = False
        self.rtk[rtk['source']] = rtk
        # self.show_target()

    def show_target(self, img, target, host):
        indent = self.get_indent(target['source'])

        range, angle = self._calc_relatives(target, host)
        x, y = self.transform.trans_polar2rcs(angle, range, install['rtk'])
        if x == 0:
            x = 0.001
        width = 0.5
        height = 0.5
        ux, uy = self.transform.trans_gnd2raw(x, y,
                               host['hgt'] - target['hgt'] + install['video']['height'] - install['rtk']['height'],
                                              'rtk')
        w = 1200 * width / x
        if w > 50:
            w = 50

        h = w

        p1 = int(ux - 0.5 * w), int(uy)
        p2 = int(ux + 0.5 * w), int(uy)
        p3 = int(ux), int(uy - 0.5 * h)
        p4 = int(ux), int(uy + 0.5 * h)

        if angle > 90 or angle < -90:
            BaseDraw.draw_text(img, 'RTK target on the back', (int(ux + 4), int(uy - 4)), 0.6, CVColor.White, 1)
            return
        # cv2.line(img, p1, p2, CVColor.Green if target['rtkst'] >= 48 else CVColor.Grey, 2)
        # cv2.line(img, p3, p4, CVColor.Green if host['rtkst'] >= 48 else CVColor.Grey, 2)

        cv2.line(img, p1, p2, CVColor.Green, 2)
        cv2.line(img, p3, p4, CVColor.Green, 2)

        BaseDraw.draw_text(img, 'R: {:.3f}'.format(range), (int(ux + 4), int(uy - 4)), 0.4, CVColor.White, 1)
        BaseDraw.draw_text(img, 'A: {:.2f}'.format(angle), (int(ux + 4), int(uy + 14)), 0.4, CVColor.White, 1)
        BaseDraw.draw_text(img, 'Trange: {:.3f} angle:{:.2f}'.format(range, angle), (indent + 2, 140), 0.5,
                           CVColor.White, 1)
        return range, angle

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

    def show_lane_ipm(self, img, ratios, r=60, color=CVColor.Cyan):
        """绘制车道线
        Args:
            img: 原始图片
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            width: float 车道线宽度
            color: CVColor 车道线颜色
        """
        p = self.transform.getp_ipm_from_poly(ratios, r, 1)

        for i in range(1, len(p) - 1, 1):
            BaseDraw.draw_line(img, p[i], p[i + 1], color, 2)

    def draw_vehicle_state(self, img, data):
        # indent = self.get_indent(data['source'])
        if len(data) == 0:
            return
        if 'speed' in data:
            self.show_veh_speed(img, data['speed'], data['source'])
        if 'yaw_rate' in data:
            self.show_yaw_rate(img, data['yaw_rate'], data['source'])

    def draw_obs(self, img, data, ipm):
        if len(data) == 0:
            return
        if data['type'] != 'obstacle':
            return

        x = data['pos_lon']
        y = data['pos_lat']

        color = self.color_seq[data['color']]
        width = 0.4
        otype = 0
        if data['color'] == 1:
            otype = 2

        if 'class' in data:
            width = data['width']
            otype = data['class']

        if 'cipo' in data and data['cipo']:
            color = CVColor.Yellow
            self.show_cipo_info(img, data)

        self.show_obs(img, data, color)
        # self.show_ipm_obs(ipm, otype, x, y, data['id'])
        # self.show_ipm_obs(ipm, data)

    # def draw_can_data(self, img, data, ipm):
    #     if data['type'] == 'obstacle':
    #         self.draw_obs(img, data, ipm)
    #     elif data['type'] == 'lane':
    #         self.draw_lane_r(img, data)
    #     elif data['type'] == 'vehicle_state':
    #         self.show_veh_speed(img, data['speed'], data['source'])
    #     elif data['type'] == 'CIPV':
    #         self.cipv = data['id']

    def draw_rtk(self, img, data, target):
        if len(data) == 0:
            return

        self.show_rtk(img, data)
        if target:
            self.show_target(img, target, data)

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
                           '{:.2f} {:.2f}  {:.2f}'.format(install['video']['yaw'],
                                                          install['video']['pitch'],
                                                          install['video']['roll']),
                           (1180, 710), 0.3, CVColor.White, 1)

    def show_warning(self, img, title):
        # print(title)
        if isinstance(title, list):
            for idx, t in enumerate(title):
                # print(idx)
                BaseDraw.draw_text(img, t, (10, 200 + idx*80), 2, CVColor.Red, 3)
        else:
            BaseDraw.draw_text(img, title, (10, 200), 2, CVColor.Red, 3)

    def show_ub482_common(self, img, data):
        indent = self.get_indent(data['source'])
        # print(data['type'], data['ts'], data['sol_stat'], data['pos_type'])
        # self.update_column_ts(data['source'], data['ts'])
        color = CVColor.White
        style_list = {'NONE': 'fail', 'DOPPLER_VELOCITY': 'pass', 'NARROW_INT': 'pass'}
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
            #
            # vel = (data['velN'] ** 2 + data['velE'] ** 2) ** 0.5
            # BaseDraw.draw_text(img, '{:.2f}km/h'.format(vel * 3.6), (indent + 142, 120), 0.5, color, 1)
        if data['type'] == 'heading':
            # BaseDraw.draw_text(img, '{}'.format(data['pos_type']), (indent + 2, 40), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'yaw: {:.2f}'.format(data['yaw']), (indent + 2, 60), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'pitch: {:.2f}'.format(data['pitch']), (indent + 2, 80), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'len: {:.3f}'.format(data['length']), (indent + 2, 100), 0.5, color, 1)
            self.show_text_info(data['source'], 140, 'H:{}'.format(data['pos_type']), style_list.get(data['pos_type']))
            self.show_text_info(data['source'], 180, 'Yaw  Pitch Len '.format(data['yaw']))
            self.show_text_info(data['source'], 200, '{:.2f} {:.2f} {:.2f}'.format(data['yaw'], data['pitch'], data['length']))
            self.show_text_info(data['source'], 160, '#SVs/sol: {}/{}'.format(data['#SVs'], data['#solSVs']))
            # self.show_text_info(data['source'], 180, 'len: {:.3f}'.format(data['length']))
        if data['type'] == 'bestvel':
            # BaseDraw.draw_text(img, 'V:{}'.format(data['pos_type']), (indent + 2, 120), 0.5, color, 1)
            self.show_text_info(data['source'], 220, 'V:{}'.format(data['pos_type']), style_list.get(data['pos_type']))

        if data['type'] == 'rtcm':
            BaseDraw.draw_text(img, 'rtcm rcv:{}'.format(data['len']), (indent + 82, 20), 0.5, color, 1)

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

    def show_ipm_target(self, img, target, host):
        range, angle = self._calc_relatives(target, host)
        x, y = self.transform.trans_polar2rcs(angle, range)
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

        cv2.line(img, p1, p2, CVColor.Green, 2)
        cv2.line(img, p3, p4, CVColor.Green, 2)

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

        if 'color' in data:
            color = self.color_seq[data['color']]
        else:
            color = CVColor.Blue
        # self.show_lane(img, (data['a0'], data['a1'], data['a2'], data['a3']), data['range'], color=color)
        # lane message
        self.show_lane(img, data, (data['a0'], data['a1'], data['a2'], data['a3']), data['range'], color=color)

    def draw_lane_ipm(self, img, data):
        if len(data) == 0:
            return
        if data['type'] != 'lane':
            return

        if 'color' in data:
            color = self.color_seq[data['color']]
        else:
            color = CVColor.Blue

        self.show_lane_ipm(img, (data['a0'], data['a1'], data['a2'], data['a3']),
                           data['range'], color)