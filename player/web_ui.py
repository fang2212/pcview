import collections
import sys
import queue
import threading
import asyncio

import aiohttp
import websockets
import msgpack
import eclient
import sharemem

import time
from datetime import datetime

import cv2
import numpy as np
from math import *

# from config.config import install
from player.eclient_ui import BaseDraw, CVColor
from player.ui import FlatColor, color_dict
from tools.geo import gps_bearing, gps_distance
from tools.transform import Transform
# import roadmarking_pb2


class Player(object):
    """图片播放器"""

    def __init__(self, uniconf):
        self.transform = Transform(uniconf)
        self.cfg = uniconf

        self.video_streams = {'video': {}}
        # self.img_width = 1280
        # self.img_height = 960
        self.img_width = 1920
        self.img_height = 1080
        self.columns = {'video': {'indent': 0, 'y0': 0, 'h': 1000, 'buffer': {}, 'ts': 0}}
        self.param_bg_width = 160
        self.next_patch_x = 160
        self.next_patch_y = 0
        self.ts_now = 0
        self.rtk = {}
        self.lr = 0

        self.start_time = datetime.now()
        self.pxs = None

        self.detection_color = {
            'Unknown': 'fail',
            'SingleTrack': 'pass',
            'MultipleTrack': 'pass',
            'Vision Only': 'pass',
            'Radar And Vision': 'pass'
        }

        self.param_bg_width = 160

    def draw_img(self, img):
        """
        绘制图像
        :param img:
        :return:
        """
        BaseDraw.draw_img(img)

    def clear(self):
        """
        绘制图像
        :param img:
        :return:
        """
        BaseDraw.clear()

    def get_indent(self, source):
        if not self.columns.get(source):
            self.add_column(source)
        return self.columns[source]['indent']

    def add_column(self, source):
        self.columns[source] = {
            'indent': self.next_patch_x,
            'y0': self.next_patch_y,
            "color": color_dict.get(source.split('.')[0], color_dict["default"]),
            "buffer": dict(),
            "ts": 0,
            "h": 1000
        }

        self.next_patch_x += self.param_bg_width

    def show_dist_mark_ipm(self, img):
        BaseDraw.draw_grid_3d()

    def show_parameters_background(self, img, rect, color=BaseDraw.bgr_to_str(CVColor.Black, 0.6), border_color=BaseDraw.bgr_to_str(CVColor.LightGray), border_width=0):
        """左上角参数背景图"""
        BaseDraw.draw_alpha_rect(img, rect, color, border_color, border_width)

    def show_obs(self, img, obs, thickness=2):
        """
        显示目标对象
        :param img:
        :param obs:
        :param thickness:
        :return:
        """
        source = obs['source'].split('.')[0]
        sensor = obs.get('sensor') or source
        color = BaseDraw.bgr_to_str(color_dict.get(source, color_dict['default']))

        width = obs.get('width', 0.3)
        height = obs.get('height', width)
        # 如果是行人的话固定高度
        if obs.get('class') == 'pedestrian':
            height = 1.6

        # 计算目标坐标
        if 'range' in obs:
            dist = obs['range']
            x, y = self.transform.trans_polar2rcs(obs['angle'], obs['range'], sensor)
        elif 'pos_lon' in obs and 'pos_lat' in obs:
            x, y = self.transform.compensate_param_rcs(obs['pos_lon'], obs['pos_lat'], sensor)
            dist = (x ** 2 + y ** 2) ** 0.5
        else:
            print('no x dis in obs:', obs)
            return
        dist = max(0.1, dist)
        if dist <= 0 or x <= 0:
            return

        w = self.cfg.installs['video']['fu'] * width / dist
        w = min(600, w)
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

        size = 16
        if obs.get('sensor_type') == 'radar':
            # 绘制雷达目标圆圈
            w = max(5, min(50, w))
            h = max(5, min(50, h))

            BaseDraw.draw_circle((int(x0), int(y0 - 0.5 * h)), radius=int(w), border_color=color, thickness=1)
            BaseDraw.draw_text('{}'.format(obs['id']), (x1 + int(1.4 * w), y1 + int(1.4 * w)), size, color, 1)
        elif obs.get('class') == 'pedestrian':
            # 绘制行人目标框
            if x1 < 0 or y1 < 0 or x2 > self.img_width or y2 > self.img_height:
                return
            alpha_color = BaseDraw.covert_alpha(color, 0.3)
            BaseDraw.draw_rect((x1, y1), (x2, y2), alpha_color, border_color=color, border=2)
            BaseDraw.draw_text('{}'.format(obs['id']), (x1 - 2, y1 - 4), size, color, 1)
        else:
            # 默认车辆框
            BaseDraw.draw_rect_corn(img, (x1, y1), (x2, y2), color, thickness)
            BaseDraw.draw_text('{}'.format(obs['id']), (x1 - 2, y1 - 4), size, color, 1)

        if 'cipo' in obs and obs['cipo']:
            # 更新关键车信息
            self.show_cipo_info(img, obs)
            # 绘制关键车目标
            BaseDraw.draw_arrow((x0, y0 + 3), (x0, y0 + 24), BaseDraw.bgr_to_str(CVColor.Yellow), tail_width=4, head_width=16, head_length=8)

    def show_ipm_obs(self, img, obs):
        pass

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
        if len(p) <= 1:
            return
        dash = ''
        if style == "dotted":
            dash = [10, 5]
        BaseDraw.draw_polyline(p[1:], dash, color, 2)

        a0, a1, a2, a3 = ratios
        if abs(a0) < 5:
            x = 12
        else:
            x = 25
        y = a0 + a1 * x + a2 * x ** 2 + a3 * x ** 3

        tx, ty = self.transform.trans_gnd2raw(x, y)
        text_step = 15
        if 'type_class' in data:
            BaseDraw.draw_text('class: {}'.format(data['type_class']), (tx - 50, ty), 16, color, 1)

        if 'prediction_source' in data:
            BaseDraw.draw_text('predict: {}'.format(data['prediction_source']), (tx - 50, ty + text_step), 16,
                               color, 1)

        if 'probability' in data:
            BaseDraw.draw_text('prob: ' + str('%.2f' % data['probability']), (tx - 50, ty + text_step * 2),
                               16, color, 1)

    def show_tsr(self, img, data):
        pass

    def show_text_info(self, source, height, text, style='normal', expire_ts=None):
        if style is None:
            style = 'warning'
        self.get_indent(source)
        self.columns[source]['buffer'][height] = {'text': text, 'style': style, 'expire_ts': expire_ts}

    def update_column_ts(self, source, ts):
        if not source:
            return
        if not self.columns.get(source):
            self.add_column(source)
        self.columns[source]['ts'] = ts

    def render_text_info(self, img):
        w = self.param_bg_width
        slots = {}
        # 在图片宽度内按单个状态框的宽度划分记录状态框的高度
        for i in range(0, self.img_width, w):
            slots[i] = 0

        for idx, col in enumerate(self.columns):
            indent = sorted(slots, key=lambda x: slots[x])[0]
            y0 = slots[indent]
            entry = self.columns[col]
            h = max(self.columns[col]['buffer']) + 4 if self.columns[col]['buffer'] else 24
            h = 24 if h == 0 else h
            self.columns[col]['indent'] = indent
            self.columns[col]['y0'] = y0
            self.columns[col]['h'] = h
            slots[indent] = y0 + h + 4

            color_lg = BaseDraw.bgr_to_str(self.columns[col].get('color', CVColor.LightGray))
            self.show_parameters_background(img, (indent, y0, w if w <= self.img_width else self.img_width, h), border_color=color_lg, border_width=2)
            BaseDraw.draw_status_indent((indent + 10, y0 + 11), 12, color_lg)
            if 'ifv300' in col:
                BaseDraw.draw_text('q3', (indent + 24, y0 + 18), 16, BaseDraw.bgr_to_str(CVColor.Cyan), 1)
            else:
                BaseDraw.draw_text(col, (indent + 24, y0 + 18), 16, BaseDraw.bgr_to_str(CVColor.Cyan), 1)
            dt = self.ts_now - self.columns[col]['ts']

            if dt > 999:
                delay_ms = ">+999s"
            elif dt < -999:
                delay_ms = "<-999s"
            elif dt >= 1 or dt <= -1:
                delay_ms = "{:+4d}s".format(int(dt))
            else:
                delay_ms = '{:>+4d}ms'.format(int(dt * 1000))

            BaseDraw.draw_text(delay_ms, (indent + 92, y0 + 18), 16, BaseDraw.bgr_to_str(CVColor.White), 1)

            for height in entry['buffer']:
                if not entry['buffer'][height]:
                    continue
                if entry['buffer'][height].get('expire_ts') and entry['buffer'][height].get('expire_ts') < time.time():
                    entry['buffer'][height].clear()
                    continue
                # print(col, height, entry['buffer'])
                # 字体颜色
                color = BaseDraw.bgr_to_str(CVColor.White)
                style = entry['buffer'][height]['style']
                style_list = {'normal': None, 'warning': CVColor.Yellow, 'fail': CVColor.Red, 'pass': CVColor.Green}
                if isinstance(style, str) and style_list.get(style):
                    if style in style_list:
                        color = BaseDraw.bgr_to_str(style_list.get(style))
                    else:
                        if style == 'critical':
                            pass
                elif isinstance(style, tuple):
                    color = BaseDraw.bgr_to_str(style)
                BaseDraw.draw_text(entry['buffer'][height]['text'], (entry['indent'] + 2, height + y0), 16, color, 1)

    def show_video_info(self, img, data):
        tnow = data['ts']
        if data['source'] not in self.video_streams:
            self.video_streams[data['source']] = {'frame_cnt': data['frame_id'] - 1, 'last_ts': 0, 'ts0': time.time(),
                                                  'fps': 20}
        if tnow == self.video_streams[data['source']]['last_ts']:
            return
        self.show_parameters_background(img, (0, 0, 160, 80))
        BaseDraw.draw_text(data['source'], (2, 20), 0.5, BaseDraw.bgr_to_str(CVColor.Cyan), 1)
        dt = self.ts_now - data['ts']
        BaseDraw.draw_text('{:>+4d}ms'.format(int(dt * 1000)), (92, 20), 0.5, BaseDraw.bgr_to_str(CVColor.White), 1)
        BaseDraw.draw_text('frame: {}'.format(data['frame_id']), (2, 40), 0.5, BaseDraw.bgr_to_str(CVColor.White), 1)

        self.video_streams[data['source']]['frame_cnt'] += 1
        # duration = time.time() - self.video_streams[data['source']]['ts0']
        dt = tnow - self.video_streams[data['source']]['last_ts']
        self.video_streams[data['source']]['last_ts'] = tnow
        fps = 1 / dt
        self.video_streams[data['source']]['fps'] = 0.9 * self.video_streams[data['source']]['fps'] + 0.1 * fps
        BaseDraw.draw_text('fps: {:.1f}'.format(self.video_streams[data['source']]['fps']), (2, 60), 0.5,
                           BaseDraw.bgr_to_str(CVColor.White), 1)
        BaseDraw.draw_text('lost frames: {}'.format(data['frame_id'] - self.video_streams[data['source']]['frame_cnt']),
                           (2, 80), 0.5, BaseDraw.bgr_to_str(CVColor.White), 1)
        BaseDraw.draw_text('dev: {}'.format(data['device']), (2, 100), 0.5, BaseDraw.bgr_to_str(CVColor.White), 1)

    def show_status_info(self, source, status_list):
        """
        显示状态栏信息
        style: normal, warning, fail, pass
        """
        show_line = 40          # 显示的行位置，每20像素的高度为一行
        for i in status_list:
            self.show_text_info(source, i.get("height", show_line), i.get("text", ""), i.get("style", "normal"))
            show_line = i.get("height", show_line) + 20

    def show_frame_id(self,  source, fn):
        self.show_text_info(source, 40, 'frame: ' + str(int(fn)))

    def show_pinpoint(self, pp):
        BaseDraw.draw_text('Pin: {lat:.8f} {lon:.8f} {hgt:.3f}'.format(**pp), (950, 710), 20, CVColor.White, 1)

    def show_frame_cost(self, cost):
        self.show_text_info('video', 80, 'render_cost: {}ms'.format(int(cost * 1000)))

    def show_fps(self, source, fps):
        self.show_text_info(source, 60, 'fps: ' + str(int(fps)))

    def show_datetime(self, ts=None):
        """
                视频的录制时间
                :param img:
                :param ts:
                :return:
                """
        if ts is None:
            ta = datetime.now()
        else:
            ta = time.localtime(ts)

        date = time.strftime('%Y/%m/%d', ta)
        time_ = time.strftime('%H:%M:%S', ta)
        self.show_text_info('video', 100, '{}'.format(date))
        self.show_text_info('video', 120, '{}'.format(time_))

    def show_ttc(self, img, ttc, source):
        pass

    def show_veh_speed(self, speed, source):
        self.show_text_info(source, 40, '{:.1f} km/h'.format(speed))

    def show_yaw_rate(self, yr, source):
        yr_deg = yr * 57.3
        self.show_text_info(source, 60, '{:.1f}deg/s'.format(yr_deg))

    def show_accel(self, acc, source):
        self.show_text_info(source, 80, '{:.1f}m/s^2'.format(acc))

    def show_q3_veh(self, img, speed, yr):
        pass

    def show_recording(self, info):
        if info == 0:
            self.show_text_info('video', 140, '               ')
            self.show_text_info('video', 160, '               ')
            return
        time_passed = time.time() - info
        self.show_text_info('video', 140, '***[REC]***', BaseDraw.bgr_to_str(CVColor.Red))
        self.show_text_info('video', 160, 'Rec time: {:.2f}s'.format(time_passed))

    def show_marking(self, img, start_time):
        time_passed = time.time() - start_time
        BaseDraw.draw_text('Marking time: {:.2f}s'.format(time_passed), (100, 680), 3, BaseDraw.bgr_to_str(CVColor.Green), 3)

    def show_replaying(self, dts):
        time_passed = dts
        self.show_text_info('video', 140, 'Replaying... ', BaseDraw.bgr_to_str(CVColor.Red))
        self.show_text_info('video', 160, 'replay time: {:.2f}s'.format(time_passed))

    def show_version(self, img, cfg):
        if cfg.runtime.get('build_time'):
            img_h = img.shape[0]
            BaseDraw.draw_text(cfg.runtime.get('git_version') + ' ' + cfg.runtime.get('build_time'),
                               (2, img_h - 6), 0.3, BaseDraw.bgr_to_str(CVColor.White), 1)

    def show_cipo_info(self, img, obs):
        """
        显示关键车信息
        :param img:
        :param obs:
        :return:
        """
        try:
            indent = self.get_indent(obs['source'])
        except Exception as e:
            print('Error:', obs)
            return

        color = color_dict['rtk']
        line = 100
        style = 'normal'
        expire_ts = time.time() + 0.5
        if 'x1_fusion' in obs['source'] and obs['sensor'] == 'x1':
            line = 160
            style = color_dict.get('x1_fusion_cam')
            self.show_text_info(obs['source'], line, 'CIPV_cam: {}'.format(obs['id']), style, expire_ts=expire_ts)
        elif obs.get("sensor") == "a1j_fusion" or obs.get("sensor") == "ifv300_fusion":
            line = 180
            self.show_text_info(obs['source'], line, 'CIPV_cam: {}'.format(obs['id']), style, expire_ts=expire_ts)

        elif obs.get('class') == 'pedestrian':
            line = 40
            self.show_text_info(obs['source'], line, 'CIPPed: {}'.format(obs['id']), expire_ts=expire_ts)
        elif obs.get('class') == 'object':
            self.show_text_info(obs['source'], line, 'CIPO: {}'.format(obs['id']), expire_ts=expire_ts)
        else:
            self.show_text_info(obs['source'], line, 'CIPVeh: {}'.format(obs['id']), expire_ts=expire_ts)

        if "detection_sensor" in obs:
            self.show_text_info(obs['source'], 60, '{}'.format(obs['detection_sensor']),
                                self.detection_color.get(obs.get("detection_sensor")))
        if 'TTC' in obs:
            self.show_text_info(obs['source'], line + 20, 'TTC: ' + '{:.2f}s'.format(obs['TTC']), style, expire_ts=expire_ts)
        dist = obs.get('pos_lon') if 'pos_lon' in obs else obs['range']
        angle = obs.get('angle') if 'angle' in obs else atan2(obs['pos_lat'], obs['pos_lon']) * 180 / pi
        self.show_text_info(obs['source'], line + 40, 'R/A: {:.2f} / {:.2f}'.format(dist, angle), style, expire_ts=expire_ts)

        BaseDraw.draw_arrow((indent + 100, line - 18), (indent + 100, line), color=color, tail_width=6)

    def show_heading_horizen(self, img, rtk):
        pass

    def show_track_gnd(self, img, rtk):
        pass

    def show_warning(self, img, data):
        pass

    def _show_drtk(self, img, rtk):
        pass

    def show_target(self, img, target, host):
        pass

    def show_rtk_target(self, img, target):
        pass

    def show_ipm_target(self, img, target, host):
        pass

    def show_rtk_target_ipm(self, img, target):
        pass

    def show_mobile_parameters(self, img, parameters, point):
        """显示关键车参数信息
        Args:
            img: 原始图片
            parameters: List [type, index, ttc, fcw, hwm, hw, vb] 关键车参数
        """
        pass

    def draw_corners(self, img):
        pass

    def show_lane_ipm(self, img, data, color=CVColor.Cyan, style=""):
        pass

    def draw_vehicle_state(self, img, data):
        if len(data) == 0:
            return
        if 'speed' in data:
            self.show_veh_speed(data['speed'], data['source'])
        if 'TTC' in data:
            self.show_text_info(data['source'], 60, 'TTC: ' + '{:.2f}s'.format(data['TTC']))
        if 'pos_lon' in data and 'pos_lat' in data:
            dist = data.get('pos_lon') if 'pos_lon' in data else data['range']
            angle = data.get('angle') if 'angle' in data else atan2(data['pos_lat'], data['pos_lon']) * 180 / pi
            self.show_text_info(data['source'], 80, 'R/A: {:.2f} / {:.2f}'.format(dist, angle))
        if 'yaw_rate' in data:
            self.show_yaw_rate(data['yaw_rate'], data['source'])
        if 'accel' in data:
            self.show_accel(data['accel'], data['source'])

    def show_alarm_info(self, alarm_info):
        now = time.time()

        for i, key in enumerate(alarm_info):
            if alarm_info[key] > now:
                BaseDraw.draw_text(key, (10, i*60 + 300), 30, "rgb(0, 0, 255)", 2)

    def cal_fps(self, frame_cnt):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        duration = duration if duration > 0 else 1
        fps = frame_cnt / duration
        return fps

    def show_intrinsic_para(self, img):
        pass

    def show_failure(self, failure):
        pass

    def show_warning_ifc(self, img, title):
        if isinstance(title, list):
            for idx, t in enumerate(title):
                BaseDraw.draw_text(t, (10, 200 + idx * 80), 2, CVColor.Red, 3)
        else:
            BaseDraw.draw_text(title, (10, 200), 2, CVColor.Red, 3)

    def show_ub482_common(self, img, data):
        pass

    def show_rtk_pva(self, img, data):
        pass

    def show_gps(self, data):
        pass

    def show_rtcm(self, data):
        pass

    def _calc_relatives(self, target, host):
        pass

    def get_alert(self, vehicle_data, lane_data, ped_data):
        pass

    def draw_lane_r(self, img, data):
        if len(data) == 0:
            return
        if data['type'] != 'lane':
            return

        color = BaseDraw.bgr_to_str(color_dict.get(data['source'].split('.')[0], color_dict['default']))
        self.show_lane(img, data, color=color, style=data.get("style"))

    def draw_lane_ipm(self, img, data):
        pass

    def show_host_path(self, img, spd, yr, yrbias=0.0017, cipv_dist=200.0):
        pass

    def show_host_path_ipm(self, img, spd, yr, yrbias=0.0017):
        pass

    def submit(self):
        BaseDraw.submit()


