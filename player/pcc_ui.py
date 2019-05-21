from player.ui import BaseDraw, pack, logodir, CVColor
from config.config import install, config
import cv2
from tools.transform import trans_gnd2raw, trans_gnd2ipm, trans_polar2rcs
from datetime import datetime
import time
from tools.geo import gps_bearing, gps_distance
import numpy as np
import logging
import json

# logging.basicConfig函数对日志的输出格式及方式做相关配置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


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

        self.indent = 140
        self.columns = {'video': {'indent': 0}}
        self.param_bg_width = 160
        self.ts_now = 0
        self.rtk = {}

        self.start_time = datetime.now()
        self.cipv = 0

        self.color_seq = [CVColor.White, CVColor.Red, CVColor.Green, CVColor.deeporange, CVColor.purple,
                          CVColor.Blue, CVColor.LightBlue]
        self.color_obs = {'ifv300': CVColor.White,
                     'esr': CVColor.Red,
                     'lmr': CVColor.Green,
                     'x1': CVColor.purple,
                     'rtk': CVColor.Green,
                     'ars': CVColor.Blue}

        self.param_bg_width = 160

        # for col in self.columns:
        #     if len(col) == 0:
        #         del self.columns[col]
        print(self.columns)

    def add_info_column(self, msg_type):
        if len(msg_type) == 0:
            # self.columns.remove(col)
            # del self.columns[i]
            return
        else:
            self.columns[msg_type] = {'indent': self.indent}
            if 'rtk' in msg_type:
                self.indent += 300
            else:
                self.indent += 140
            for src_type in self.color_obs:
                if msg_type.split('.')[0] in src_type:
                    self.columns[msg_type]['color'] = self.color_obs[src_type]
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
                p1 = trans_gnd2ipm(i, -10)
                p2 = trans_gnd2ipm(i, 10)
                BaseDraw.draw_line(img, p1, p2, color_type=CVColor.Midgrey, thickness=1)
                BaseDraw.draw_text(img, '{}m'.format(i), p2, 0.3, CVColor.White, 1)

    def show_overlook_background(self, img):
        """绘制俯视图的背景，包括背景图，车背景图，光线图

        Args:
            img: 原始图片
        """
        y_background, x_background, _ = self.overlook_background_image.shape
        y_img, x_img, _ = img.shape
        roi_img = img[0: y_background, x_img - x_background: x_img]
        cv2.addWeighted(self.overlook_background_image, 1, roi_img, 0.4, 0.0, roi_img)
        x_center, y_center = 1144, 240

        data_r = int(1) % 20 + 120

        draw_r = []
        while data_r > 30:
            draw_r.append(data_r)
            data_r = data_r - 20
        draw_r.append(140)

        y_circle, x_circle, _ = self.circlesmall_image.shape
        for R in draw_r:
            x_new, y_new = int(R), int(y_circle * R / x_circle)
            new_circle = cv2.resize(self.circlesmall_image, (y_new, x_new),
                                    interpolation=cv2.INTER_CUBIC)
            x_begin = x_center - x_new // 2
            x_end = x_begin + x_new
            y_begin = y_center - y_new // 2
            y_end = y_begin + y_new
            roi_img = img[y_begin: y_end, x_begin: x_end]
            cv2.addWeighted(new_circle, 0.5, roi_img, 1.0, 0.0, roi_img)

        for sector_in in [self.sectorwide_image, self.sectorthin_image]:
            y_sector, x_sector, _ = sector_in.shape
            x_begin = 1145 - x_sector // 2
            x_end = x_begin + x_sector
            y_end = 219
            y_begin = y_end - y_sector
            roi_img = img[y_begin: y_end, x_begin: x_end]
            cv2.addWeighted(sector_in, 0.5, roi_img, 1.0, 0.0, roi_img)

        y_car, x_car, _ = self.car_image.shape
        x_begin = x_center - x_car // 2 - 3
        x_end = x_begin + x_car
        y_begin = y_center - y_car // 2
        y_end = y_begin + y_car
        roi_img = img[y_begin: y_end, x_begin: x_end]
        cv2.addWeighted(self.car_image, 1.0,
                        roi_img, 1.0, 0.0, roi_img)

    def show_parameters_background(self, img, rect):
        """左上角参数背景图"""
        BaseDraw.draw_alpha_rect(img, rect, 0.4)

    def show_columns(self, img):
        w = self.param_bg_width
        self.show_parameters_background(img, (0, 0, w if w <= 1280 else 1280, 150))
        for col in self.columns:
            indent = self.columns[col]['indent']
            BaseDraw.draw_text(img, col, (indent + 12, 20), 0.5, CVColor.Cyan, 1)
            if col is not 'video':
                cv2.rectangle(img, (indent, 10), (indent + 10, 20), self.columns[col]['color'], -1)

    def show_vehicle(self, img, position, id=0, dist=0, color=CVColor.Cyan, thickness=2):
        """绘制车辆框
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            color: CVColor 车辆颜色
            thickness: int 线粗
        """

        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        BaseDraw.draw_rect_corn(img, (x1, y1), (x2, y2), color, thickness)
        # BaseDraw.draw_rect(img,  (x1, y1), (x1 + 70, y1 - 12), color,-1)
        BaseDraw.draw_text(img, 'id:{} {:.1f}'.format(id, dist), (x1, y1), 0.4, CVColor.Black, 1)
        # BaseDraw.draw_text(img, '{}'.format(type), (x1, y2+14), 0.4, CVColor.Green, 1)

    def show_vehicle_info(self, img, position, vertical_dis, horizontal_dis, vehicle_width, vehicle_type):
        """绘制车辆信息
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            vertical_dis: float 与检测车辆的竖直距离
            horizontal_dis: float 与检测车辆的水平距离
            vehicle_width: float 检测车辆的宽度
            vehicle: str 车辆类型，见const_type
        """
        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        origin_x = max(0, x2 - 150)
        origin_y = max(0, y1 - 30)
        BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 150, 30), 0.6)
        size = 1
        const_type = {
            '2': 'CAR',
            '3': 'BUS',
            '4': 'BOX',
            '5': 'SSP'
        }
        BaseDraw.draw_text(img, const_type[vehicle_type], (x2 - 150, y1 - 5),
                           size, CVColor.White, 1)

        d1 = int(float(vertical_dis) * 100) / 100
        d2 = int(float(horizontal_dis) * 10) / 10
        # data = str(d1) + ',' + str(d2)
        data = str(d1)
        BaseDraw.draw_text(img, data, (x2 - 90, y1 - 5), size, CVColor.White, 1)

        # vehicle_width = '%.2f' % vehicle_width
        # BaseDraw.draw_text(img, str(vehicle_width), (x2 - 50, y1 - 5), 0.5, CVColor.White, 1)

    def show_overlook_vehicle(self, img, type, x, y):
        """在俯视图绘制车辆
        Args:
            img: 原始图片
            type: 是否关键车
            y: float 与检测车辆的竖直距离
            x: float 与检测车辆的水平距离
        """

        d_y = int(float(y))
        d_x = int(float(x))
        x_car = max(20, 190 - d_x * 2)
        typ = int(type)
        if typ == 0:
            car = self.overlook_othercar_image
        elif type == 2:  # keycar
            car = self.overlook_beforecar_image

        y_car = 1144 + int(10 * d_y)

        x_shape, y_shape, _ = car.shape
        x_begin = x_car - x_shape // 2
        x_end = x_begin + x_shape
        y_begin = y_car - y_shape // 2
        y_end = y_begin + y_shape

        roi_img = img[x_begin: x_end, y_begin: y_end]
        cv2.addWeighted(car, 0.5, roi_img, 1.0, 0.0, roi_img)

    def show_obs(self, img, obs, color=CVColor.Cyan, thickness=2):
        indent = self.get_indent(obs['source'])
        color = obs.get('color')
        if color:
            color = self.color_seq[color]
        else:
            color = self.color_seq[0]

        width = obs.get('width')
        width = width if width else 0.3
        height = obs.get('height')
        # print(obs['source'], obs['class'])
        height = height if height else width
        if obs.get('class') == 'pedestrian':
            height = 1.6
        if 'pos_lon' in obs:
            x = obs['pos_lon']
            y = obs['pos_lat']
        else:
            # print(obs['source'].split('.')[0])
            x, y = trans_polar2rcs(obs['angle'], obs['range'], install[obs['source'].split('.')[0]])
        if x == 0:
            x = 0.1
        if x < 0:
            return

        w = 1200 * width / x
        if w > 600:
            w = 600
        x0, y0 = trans_gnd2raw(x, y)

        h = w
        # if obs.get('class') == 'pedestrian':
        h = 1200 * height / x
        # ux - 0.5 * w, uy - w, w, w
        # print(obs.get('class'))
        x1 = x0 - 0.5 * w
        y1 = y0 - h
        # width = int(width)
        # height = int(height)
        x2 = x1 + w
        y2 = y1 + h
        # print(obs['source'], w, h)
        x1 = int(x1)
        x2 = int(x2)
        y1 = int(y1)
        y2 = int(y2)
        if obs.get('sensor') == 'radar':
            if w > 50:
                w = 50
            # print(int(x1), int(y1), int(w), width)
            cv2.circle(img, (int(x0), int(y0)), int(w), color, 1)
        elif obs.get('class') == 'pedestrian':
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        else:
            BaseDraw.draw_rect_corn(img, (x1, y1), (x2, y2), color, thickness)
        # BaseDraw.draw_rect(img,  (x1, y1), (x1 + 70, y1 - 12), color,-1)
        BaseDraw.draw_text(img, 'id:{} {:.1f}'.format(obs['id'], obs['pos_lon'] if 'pos_lon' in obs else obs['range']),
                           (x1, y1), 0.4, CVColor.White, 1)

        if 'cipo' in obs and obs['cipo']:
            # color = CVColor.Yellow
            self.show_cipo_info(img, obs)
            BaseDraw.draw_up_arrow(img, x0, y0+3, color)

        # if 'TTC' in obs:
        #     self.show_ttc(img, obs['TTC'], obs['source'])

    def show_ipm_obs(self, img, obs):
        id = obs['id']
        if 'pos_lon' in obs:
            x = obs['pos_lon']
            y = obs['pos_lat']
        else:
            x, y = trans_polar2rcs(obs['angle'], obs['range'], install[obs['source'].split('.')[0]])
        u, v = trans_gnd2ipm(x, y)
        # color = CVColor.Green
        # if type == 0:
        #     color = CVColor.Green
        # elif type == 2:
        #     color = CVColor.Red
        color = self.color_seq[obs['color']]

        if obs.get('sensor') == 'radar':
            cv2.circle(img, (u, v), 8, color, 2)
        else:
            cv2.rectangle(img, (u - 8, v - 16), (u + 8, v), color, 2)
        BaseDraw.draw_text(img, '{}'.format(id), (u + 10, v + 3), 0.4, color, 1)


    def show_vehicle_parameters(self, img, parameters, point):
        """显示关键车参数信息
        Args:
            img: 原始图片
            parameters: List [type, index, ttc, fcw, hwm, hw, vb] 关键车参数
        """
        type = parameters[0]
        index = parameters[1]
        ttc = parameters[2]
        fcw = parameters[3]
        hwm = parameters[4]
        hw = parameters[5]
        vb = parameters[6]

        origin_x, origin_y = point
        gap_v = 20
        BaseDraw.draw_text(img, 'vechicle', (origin_x, origin_y + gap_v), 0.5, CVColor.Cyan, 1)
        BaseDraw.draw_text(img, 'type:' + type, (origin_x, origin_y + gap_v * 2), 0.5, CVColor.White, 1)
        # BaseDraw.draw_text(img, 'index:' + index, (origin_x, origin_y + gap_v*3), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'ttc:' + ttc, (origin_x, origin_y + gap_v * 3), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'fcw:' + fcw, (origin_x, origin_y + gap_v * 4), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'hwm:' + hwm, (origin_x, origin_y + gap_v * 5), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'hw:' + hw, (origin_x, origin_y + gap_v * 6), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'vb:' + vb, (origin_x, origin_y + gap_v * 7), 0.5, CVColor.White, 1)


    def show_lane(self, img, ratios, r=60, color=CVColor.Cyan):
        """绘制车道线
        Args:
            img: 原始图片
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            width: float 车道线宽度
            color: CVColor 车道线颜色
        """

        a0, a1, a2, a3 = ratios
        a0 = float(a0)
        a1 = float(a1)
        a2 = float(a2)
        a3 = float(a3)

        p = []

        for x in range(int(r)):
            # x1 = x
            # x2 = x1 + 1
            y = a0 + a1 * x + a2 * x ** 2 + a3 * x ** 3
            # y2 = a0 + a1 * x2 + a2 * x2 ** 2 + a3 * x2 ** 3
            tx, ty = trans_gnd2raw(x, y)
            # tx2, ty2 = trans_gnd2raw(x2, y2)
            p.append((int(tx), int(ty)))

        for i in range(1, len(p) - 1, 1):
            BaseDraw.draw_line(img, p[i], p[i + 1], color, 2)

    def show_lane_info(self, img, ratios, index, width, type, conf, color):
        """绘制车道线信息
        Args:
            img: 原始数据
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            index: 车道索引
            width: float 车道线宽度
            type: 车道线类型
            conf: 置信度
            color: CVColor 车道线颜色
        """
        a0, a1, a2, a3 = ratios
        a0 = float(a0)
        a1 = float(a1)
        a2 = float(a2)
        a3 = float(a3)

        color = CVColor.Cyan
        size = 1
        y1 = 500
        x1 = (int)(a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1)
        # BaseDraw.draw_text(img, 'index:' + str(index), (x1, y1-45), 0.5, color, 1)
        width = '%.2f' % width
        BaseDraw.draw_text(img, 'width:' + str(width), (x1, y1 - 20), size, color, 1)
        BaseDraw.draw_text(img, 'type:' + str(type), (x1, y1), size, color, 1)
        # BaseDraw.draw_text(img, 'conf:' + str(conf), (x1, y1), 0.5, color, 1)

    def show_overlook_lane(self, img, ratios, r=60):
        """在俯视图绘制车道线
        Args:
            img: 原始数据
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            color: CVColor 车道线颜色
        """
        a0, a1, a2, a3 = ratios
        a0 = float(a0)
        a1 = float(a1)
        a2 = float(a2)
        a3 = float(a3)

        for y in range(0, int(r), 1):
            y1 = y
            y2 = y1 + 2
            x1 = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            x2 = a0 + a1 * y2 + a2 * y2 * y2 + a3 * y2 * y2 * y2
            x1 = 1144 + int(x1 * 10)
            x2 = 1144 + int(x2 * 10)
            y1 = 240 - y1 * 2
            y2 = 240 - y2 * 2
            BaseDraw.draw_line(img, (x1, y1), (x2, y2), CVColor.Cyan, 1)

    def show_lane_parameters(self, img, parameters, point):
        """显示车道线参数
        Args:
            img: 原始图像
            parameters: List [lw_dis, rw_dis, ldw, trend] 车道线信息
        """
        lw_dis = parameters[0]
        rw_dis = parameters[1]
        ldw = parameters[2]
        trend = parameters[3]

        origin_x, origin_y = point
        gap_v = 20
        BaseDraw.draw_text(img, 'lane', (origin_x, origin_y + gap_v), 0.5, CVColor.Cyan, 1)
        BaseDraw.draw_text(img, 'lw_dis:' + lw_dis, (origin_x, origin_y + gap_v * 2), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'rw_dis:' + rw_dis, (origin_x, origin_y + gap_v * 3), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'ldw:' + ldw, (origin_x, origin_y + gap_v * 4), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'trend:' + trend, (origin_x, origin_y + gap_v * 5), 0.5, CVColor.White, 1)

    def show_peds(self, img, position, color=CVColor.Cyan, thickness=2):
        """绘制pedestrain
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            color: CVColor 颜色
            thickness: int 线粗
        """

        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        BaseDraw.draw_rect(img, (x1, y1), (x2, y2), color, thickness)

    def show_peds_info(self, img, position, distance):
        """绘制车辆信息
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            max_speed: float
        """
        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        origin_x = max(0, x2 - 65)
        origin_y = max(0, y1 - 30)
        font_size = 1
        BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 65, 30), 0.6)
        BaseDraw.draw_text(img, ('%.1f' % distance), (x2 - 65, y1 - 5),
                           font_size, CVColor.White, 1)

    def show_tsr(self, img, position, color=CVColor.Cyan, thickness=2):
        """绘制tsr框
        Args:
            img: 原始图片
            position: (x, y, width, height),框的位置，大小
            color: CVColor 颜色
            thickness: int 线粗
        """

        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        BaseDraw.draw_rect(img, (x1, y1), (x2, y2), color, thickness)

    def show_tsr_info(self, img, position, max_speed):
        """绘制车辆信息
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            max_speed: float
        """
        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        origin_x = max(0, x2 - 40)
        origin_y = max(0, y2)
        BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 40, 20), 0.6)
        BaseDraw.draw_text(img, str(max_speed), (x2 - 30, y2 + 5),
                           1, CVColor.Green, 1)

    def show_tsr_parameters(self, img, parameters, point):
        """显示tsr信息
        Args:
            img: 原始图片
            parameters: List [index, TODO ]
        """
        index = parameters[0]
        speed_limit = parameters[1]
        warning_level = parameters[2]
        warning_state = parameters[3]

        origin_x, origin_y = point
        gap_v = 20
        size = 0.5
        BaseDraw.draw_text(img, 'tsr', (origin_x, origin_y + gap_v), size, CVColor.Cyan, 1)
        BaseDraw.draw_text(img, 'focus_index:' + index, (origin_x, origin_y + gap_v * 2), size, CVColor.White, 1)
        BaseDraw.draw_text(img, 'speed_limit:' + speed_limit, (origin_x, origin_y + gap_v * 3), size, CVColor.White, 1)
        BaseDraw.draw_text(img, 'warning_level:' + warning_level, (origin_x, origin_y + gap_v * 4), size, CVColor.White,
                           1)
        BaseDraw.draw_text(img, 'warning_state:' + warning_state, (origin_x, origin_y + gap_v * 5), size, CVColor.White,
                           1)

    def show_env(self, img, speed, light_mode, fps, point):
        """显示环境信息
        Args:
            img: 原始图片
            light_mode: 白天或夜间
            fps: 帧率
        """
        origin_x, origin_y = point
        origin_x += 10
        BaseDraw.draw_text(img, 'env', (origin_x, origin_y + 20), 0.5, CVColor.Cyan, 1)
        BaseDraw.draw_text(img, 'light:' + str(light_mode), (origin_x, origin_y + 40), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'speed:' + str(int(speed)), (origin_x, origin_y + 60), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'fps:' + str(int(fps)), (origin_x, origin_y + 80), 0.5, CVColor.White, 1)

    def show_frame_id(self, img, fn):
        indent = self.columns['video']['indent']
        BaseDraw.draw_text(img, 'frn: ' + str(int(fn)), (indent + 2, 40), 0.5, CVColor.White, 1)

    def show_fps(self, img, fps):
        indent = self.columns['video']['indent']
        BaseDraw.draw_text(img, 'fps: ' + str(int(fps)), (indent + 2, 60), 0.5, CVColor.White, 1)

    def show_datetime(self, img, ts=None):
        indent = self.columns['video']['indent']
        if ts is None:
            ta = datetime.now()
        else:
            ta = time.localtime(ts)

        FORMAT = '%Y/%m/%d'
        date = time.strftime(FORMAT, ta)
        FORMAT = '%H:%M:%S'
        time_ = time.strftime(FORMAT, ta)
        BaseDraw.draw_text(img, '{}'.format(date), (indent + 2, 100), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, '{}'.format(time_), (indent + 2, 120), 0.5, CVColor.White, 1)

    def show_ttc(self, img, ttc, source):
        indent = self.columns[source]['indent']
        BaseDraw.draw_text(img, 'TTC:' + '{:.2f}s'.format(ttc), (indent + 2, 40), 0.5, CVColor.Cyan, 1)

    def show_veh_speed(self, img, speed, source):
        indent = self.columns[source]['indent']
        BaseDraw.draw_text(img, '{:.1f}km/h'.format(speed), (indent + 2, 80), 0.5, CVColor.White, 1)

    def show_yaw_rate(self, img, yr, source):
        indent = self.columns[source]['indent']
        BaseDraw.draw_text(img, 'yawr:' + '%.4f' % yr, (indent + 2, 100), 0.5, CVColor.White, 1)

    def show_q3_veh(self, img, speed, yr):
        BaseDraw.draw_text(img, 'q3spd: ' + str(int(speed * 3.6)), (2, 120), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'q3yr: ' + '%.4f' % yr, (2, 140), 0.5, CVColor.White, 1)

    def show_recording(self, img, info):
        time_passed = time.time() - info
        BaseDraw.draw_text(img, 'Recording... ', (2, 700), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'time elapsed: {:.2f}s'.format(time_passed), (2, 712), 0.5, CVColor.White, 1)


    def show_cipo_info(self, img, obs):
        indent = self.get_indent(obs['source'])
        # print(obs['class'])
        if obs.get('class') == 'pedestrian':
            line = 40
            BaseDraw.draw_text(img, 'CIPPed: {}'.format(obs['id']), (indent + 18, line), 0.5, CVColor.White, 1)
        elif obs.get('class') == 'object':
            line = 100
            BaseDraw.draw_text(img, 'CIPO: {}'.format(obs['id']), (indent + 18, line), 0.5, CVColor.White, 1)
        else:
            line = 100
            BaseDraw.draw_text(img, 'CIPVeh: {}'.format(obs['id']), (indent + 18, line), 0.5, CVColor.White, 1)

        if 'TTC' in obs:
            BaseDraw.draw_text(img, 'TTC: ' + '{:.2f}s'.format(obs['TTC']), (indent + 2, line+20), 0.5, CVColor.White, 1)
        dist = obs['pos_lon'] if 'pos_lon' in obs else obs['range']
        BaseDraw.draw_text(img, 'range: {:.2f}'.format(dist), (indent + 2, line + 40), 0.5, CVColor.White, 1)
        BaseDraw.draw_up_arrow(img, indent+8, line-12, self.color_seq[obs['color']], 6)


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
    def show_target(self, img, target, rtk):
        indent = self.columns['rtk']['indent']
        BaseDraw.draw_text(img, 'target: {:.8f} {:.8f} {:.3f}'.format(
            target['lat'], target['lon'], target['hgt']), (indent + 2, 120), 0.5, CVColor.White, 1)
        ranges = gps_distance(target['lat'], target['lon'], rtk['lat'], rtk['lon'])
        angle = gps_bearing(target['lat'], target['lon'], rtk['lat'], rtk['lon'])
        angle = angle - 180.0 - rtk['yaw']
        x, y = trans_polar2rcs(angle, ranges)
        if x == 0:
            x = 0.001
        width = 1.5
        height = 1.5
        ux, uy = trans_gnd2raw(x, y)
        w = 1200 * width / x

        h = w
        # ux - 0.5 * w, uy - w, w, w

        x1 = ux - 0.5 * w
        y1 = uy - w
        # width = int(width)
        # height = int(height)
        x2 = x1 + w
        y2 = y1 + h
        # print(obs['source'], w, h)
        x1 = int(x1)
        x2 = int(x2)
        y1 = int(y1)
        y2 = int(y2)
        cv2.rectangle(img, (x1, y1), (x2, y2), CVColor.Green, 2)
        BaseDraw.draw_text(img, 'range: {:.3f} angle {:.2f}'.format(range, angle), (indent + 2, 140), 0.5,
                           CVColor.White, 1)

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
        # print(corners)

        # if corners is None:
        #     return
        # if len(corners) == 0:
        #     return
        # 亚像素精确定位角点位置
        corners2 = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), criteria)
        d1 = np.linalg.norm(corners2[0] - corners2[6])
        d2 = np.linalg.norm(corners2[6] - corners2[48])
        print(d1, d2)
        # 图上绘制检测到的角点
        cv2.drawChessboardCorners(img, (7, 7), corners2, ret)

        # vehicle

    def draw_vehicle(self, img, vehicle_data):
        v_type, index, ttc, fcw, hwm, hw, vb = '-', '-', '-', '-', '-', '-', '-'
        if vehicle_data:
            focus_index = vehicle_data['focus_index']
            speed = vehicle_data['speed'] * 3.6
            for i, vehicle in enumerate(vehicle_data['dets']):
                focus_vehicle = (i == focus_index)
                position = vehicle['bounding_rect']
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Red if focus_index == i else CVColor.Cyan
                self.show_vehicle(img, position, color, 2)

                self.show_vehicle_info(img, position,
                                              vehicle['vertical_dist'], vehicle['horizontal_dist'],
                                              vehicle['vehicle_width'], str(vehicle['type']))
                if config.show.overlook:
                    self.show_overlook_vehicle(img, focus_vehicle,
                                                      vehicle['vertical_dist'],
                                                      vehicle['horizontal_dist'])

            if focus_index != -1:
                vehicle = vehicle_data['dets'][focus_index]
                v_type = vehicle['type']
                index = vehicle['index']
                ttc = '%.2f' % vehicle['rel_ttc']
                fcw = vehicle_data['forward_collision_warning']
                hw = vehicle_data['headway_warning']
                hwm = '%.2f' % vehicle_data['ttc']
                vb = vehicle_data['bumper_warning']
                if ttc == '1000.00':
                    ttc = '-'
            parameters = [str(v_type), str(index), str(ttc), str(fcw), str(hwm), str(hw), str(vb)]
            self.player.show_vehicle_parameters(img, parameters, (120, 0))

        # lane

    def draw_lane(self, img, lane_data):
        lw_dis, rw_dis, ldw, trend = '-', '-', '-', '-'
        if lane_data:
            speed = lane_data['speed'] * 3.6
            for lane in lane_data['lanelines']:
                if int(lane['label']) in [1, 2]:  # and speed >= config.show.lane_speed_limit:
                    color = CVColor.Cyan
                    width = lane['width']
                    l_type = lane['type']
                    conf = lane['confidence']
                    index = lane['label']
                    self.player.show_lane(img, lane['perspective_view_poly_coeff'],
                                          0.2, color)
                    if config.show.overlook:
                        self.player.show_overlook_lane(img, lane['bird_view_poly_coeff'], color)
                    self.player.show_lane_info(img, lane['perspective_view_poly_coeff'],
                                               index, width, l_type, conf, color)

            lw_dis = '%.2f' % (lane_data['left_wheel_dist'])
            rw_dis = '%.2f' % (lane_data['right_wheel_dist'])
            ldw = lane_data['deviate_state']
            trend = lane_data['deviate_trend']
            if lw_dis == '111.00':
                lw_dis = '-'
            if rw_dis == '111.00':
                rw_dis = '-'

            parameters = [str(lw_dis), str(rw_dis), str(ldw), str(trend)]
            if config.mobile.show:
                lane_y = 120 * 3
            else:
                lane_y = 120 * 2
            self.player.show_lane_parameters(img, parameters, (lane_y, 0))

        # ped

    def draw_ped(self, img, ped_data):
        if ped_data:
            for pedestrain in ped_data['pedestrians']:
                position = pedestrain['regressed_box']
                position = position['x'], position['y'], position['width'], position['height']
                # print('position:', position)
                color = CVColor.Yellow
                if pedestrain['is_key']:
                    color = CVColor.Pink
                if pedestrain['is_danger']:
                    color = CVColor.Pink
                self.player.show_peds(img, position, color, 2)
                if position[0] > 0:
                    self.player.show_peds_info(img, position, pedestrain['dist'])

    def draw_tsr(self, img, tsr_data):
        focus_index, speed_limit, tsr_warning_level, tsr_warning_state = -1, 0, 0, 0
        if tsr_data:
            logging.info('tsr data {}'.format(tsr_data))
            focus_index = tsr_data['focus_index']
            speed_limit = tsr_data['speed_limit']
            tsr_warning_level = tsr_data['tsr_warning_level']
            tsr_warning_state = tsr_data['tsr_warning_state']
            for i, tsr in enumerate(tsr_data['dets']):
                position = tsr['position']
                logging.info('tsrrrr {}'.format(position))
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Red
                self.player.show_tsr(img, position, color, 2)
                if tsr['max_speed'] != 0:
                    self.player.show_tsr_info(img, position, tsr['max_speed'])

            parameters = [str(focus_index), str(speed_limit), str(tsr_warning_level), str(tsr_warning_state)]
            self.player.show_tsr_parameters(img, parameters, (369, 0))

    def draw_lane_r(self, img, data):
        if len(data) == 0:
            return
            # print(data)
        if data['type'] != 'lane':
            return
        # self.player.show_overlook_lane(img, (data['a0'], data['a1'], data['a2'], data['a3']), data['range'])
        self.show_lane(img, (data['a0'], data['a1'], data['a2'], data['a3']), data['range'])

    def draw_vehicle_state(self, img, data):
        if len(data) == 0:
            return
        if data['type'] == 'vehicle_state':
            self.show_veh_speed(img, data['speed'])
        elif data['type'] == 'q3_vehicle':
            self.show_veh_speed(img, data['speed'], data['source'])

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

        if 'TTC' in data:
            self.show_ttc(img, data['TTC'], data['source'])

        if 'class' in data:
            width = data['width']
            otype = data['class']

        if 'cipo' in data and data['cipo']:
            color = CVColor.Yellow
            # self.player.show_ttc(img, data['TTC'], data['source'])
            self.show_cipo_info(img, data)

        # if x == 0:
        #     x = 0.1
        # w = 1200 * width / x
        # ux, uy = trans_gnd2raw(x, y)
        # self.player.show_vehicle(img, (ux - 0.5 * w, uy - w, w, w), data['id'], x, color)
        self.show_obs(img, data, color)
        # self.player.show_overlook_vehicle(img, otype, x, y)
        self.show_ipm_obs(ipm, otype, x, y, data['id'])
        # print('target {} pos_x {}'.format(data['id'], x))

        # for obj_id in list(self.vis_pos):
        #     if self.ts_now - self.vis_pos[obj_id]['ts'] > 0.2:
        #         self.vis_pos.pop(obj_id)
        #         continue
        #     self.player.show_overlook_vehicle(img, 2, self.vis_pos[obj_id]['x'], self.vis_pos[obj_id]['y'])

    def draw_can_data(self, img, data, ipm):
        if data['type'] == 'obstacle':
            self.draw_obs(img, data, ipm)
        elif data['type'] == 'lane':
            self.draw_lane_r(img, data)
        # elif data['type'] == 'q3_vehicle':
        #     self.draw_vehicle_state(img, data)
        elif data['type'] == 'vehicle_state':
            self.show_veh_speed(img, data['speed'], data['source'])
        elif data['type'] == 'CIPV':
            self.cipv = data['id']

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

    def draw_mobile(self, img, frame_id):
        index = int(frame_id / 3) * 4 + frame_id % 3
        if config.mobile.show:
            mobile_ldw, mobile_hw, mobile_fcw, mobile_vb, mobile_hwm = '-', '-', '-', '-', '-'
            mobile_log = self.mobile_content[index]
            if mobile_log:
                mobile_hwm = mobile_log.get('headway_measurement') if mobile_log.get('headway_measurement') else 0
                mobile_hw = 1 if mobile_log.get('sound_type') == 3 else 0
                mobile_fcw = 1 if mobile_log.get('sound_type') == 6 and mobile_log.get('fcw_on') == 1 else 0
                mobile_vb = 1 if mobile_log.get('sound_type') == 5 else 0
                mobile_ldw = mobile_log['left_ldw'] * 2 + mobile_log['right_ldw'] if 'left_ldw' in mobile_log else 0

            mobile_parameters = [str(mobile_hwm), str(mobile_hw), str(mobile_fcw), str(mobile_vb), str(mobile_ldw)]
            self.show_mobile_parameters(img, mobile_parameters, (120 * 2, 0))

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

        color = CVColor.White
        if data['type'] == 'bestpos':
            BaseDraw.draw_text(img, '{}'.format(data['pos_type']), (indent + 142, 40), 0.5, color, 1)
            BaseDraw.draw_text(img, 'lat: {:.8f}'.format(data['lat']), (indent + 142, 60), 0.5, color, 1)
            BaseDraw.draw_text(img, 'lon:{:.8f}'.format(data['lon']), (indent + 142, 80), 0.5, color, 1)
            BaseDraw.draw_text(img, 'hgt: {:.3f}'.format(data['hgt']), (indent + 142, 100), 0.5, color, 1)
            # vel = (data['velN'] ** 2 + data['velE'] ** 2) ** 0.5
            # BaseDraw.draw_text(img, '{:.2f}km/h'.format(vel * 3.6), (indent + 142, 120), 0.5, color, 1)
        if data['type'] == 'heading':
            BaseDraw.draw_text(img, '{}'.format(data['pos_type']), (indent + 2, 40), 0.5, color, 1)
            BaseDraw.draw_text(img, 'yaw: {:.2f}'.format(data['yaw']), (indent + 2, 60), 0.5, color, 1)
            BaseDraw.draw_text(img, 'pitch: {:.2f}'.format(data['pitch']), (indent + 2, 80), 0.5, color, 1)
            BaseDraw.draw_text(img, 'len: {:.3f}'.format(data['length']), (indent + 2, 100), 0.5, color, 1)
            # BaseDraw.draw_text(img, 'delay: {:.4f}'.format(data['ts'] - data['ts_origin']), (indent + 2, 120), 0.5, color, 1)

        if data['type'] == 'rtcm':
            BaseDraw.draw_text(img, 'rtcm rcv:{}'.format(data['len']), (indent + 82, 20), 0.5, color, 1)

    def _calc_relatives(self, target, host):
        range = gps_distance(target['lat'], target['lon'], host['lat'], host['lon'])
        angle = gps_bearing(target['lat'], target['lon'], host['lat'], host['lon'])
        angle = angle - host['yaw']
        return range, angle

    def show_ipm_target(self, img, target, host):
        range, angle = self._calc_relatives(target, host)
        x, y = trans_polar2rcs(angle, range)
        ux, uy = trans_gnd2ipm(x, y)
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


    # def show_radar(self, img, position, color=CVColor.Cyan, thickness=2):
    #     """绘制pedestrain
    #     Args:
    #         img: 原始图片
    #         position: (x, y, width, height),车辆框的位置，大小
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
    #
    # def show_radar_overlook(self, img, type, y, x):
    #     """在俯视图绘制车辆
    #     Args:
    #         img: 原始图片
    #         type: 是否关键车
    #         y: float 与检测车辆的竖直距离
    #         x: float 与检测车辆的水平距离
    #     """
    #
    #     d_y = int(float(y))
    #     d_x = int(float(x))
    #     y_car = max(20, 190 - d_y * 2)
    #     y_car = y
    #     typ = int(type)
    #     if typ == 0:
    #         car = self.overlook_othercar_image
    #     else:
    #         car = self.overlook_beforecar_image
    #     x_car = 1144 + int(10 * d_x)
    #
    #     y_shape, x_shape, _ = car.shape
    #     x_begin = x_car - x_shape // 2
    #     x_end = x_begin + x_shape
    #     y_begin = y_car - y_shape // 2
    #     y_end = y_begin + y_shape
    #
    #     roi_img = img[y_begin: y_end, x_begin: x_end]
    #     cv2.addWeighted(car, 0.5, roi_img, 1.0, 0.0, roi_img)