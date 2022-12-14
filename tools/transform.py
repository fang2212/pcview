#!/usr/bin/env python
# -*- coding: future_fstrings -*-
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/07/15
# @Author  : simon.xu
# @File    : transform.py
# @Desc    :

import json
import os
from math import *

import cv2
import numpy as np


# from config.config import install
from config.config import CVECfg


class OrientTuner(object):
    def __init__(self, uniconf):
        self.init_value = {}
        for sensor in uniconf.installs:
            self.init_value[sensor] = {}
            for item in uniconf.installs[sensor]:
                self.init_value[sensor][item] = uniconf.installs[sensor][item]
        self.transform = Transform(uniconf)
        self.cfg = uniconf

    def update_yaw(self, x, sensor='video'):
        self.cfg.installs[sensor]['yaw'] = self.init_value[sensor]['yaw'] - 0.01 * (x - 500)
        self.update_r2i()

    def update_pitch(self, x, sensor='video'):
        self.cfg.installs[sensor]['pitch'] = self.init_value[sensor]['pitch'] - 0.01 * (x - 500)
        self.update_r2i()

    def update_roll(self, x, sensor='video'):
        self.cfg.installs[sensor]['roll'] = self.init_value[sensor]['roll'] - 0.01 * (x - 500)
        self.update_r2i()

    def update_r2i(self, install_key="video"):
        self.transform.update_m_r2i(self.cfg.installs[install_key]['yaw'], self.cfg.installs[install_key]['pitch'],
                                    self.cfg.installs[install_key]['roll'])
        print('current yaw:{} pitch:{} roll:{}'.format(self.cfg.installs[install_key]['yaw'],
                                                       self.cfg.installs[install_key]['pitch'],
                                                       self.cfg.installs[install_key]['roll']))

    # def update_esr_yaw(self, x):
    #     self.esr_yaw = self.installs['esr']['yaw'] - 0.01 * (x - 500)
        # self.pitch = install['video']['pitch']
        # self.roll = install['video']['roll']

        # self.transform.update_m_r2i(self.yaw, self.pitch, self.roll)
        # print('current yaw:{} pitch:{} roll:{}'.format(self.yaw, self.pitch, self.roll))

    # def save_para(self):
    #     self.installs['video']['yaw'] = self.yaw
    #     self.installs['video']['pitch'] = self.pitch
    #     self.installs['video']['roll'] = self.roll


class Transform:
    __instance = None

    def __new__(cls, uniconf):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, uniconf):
        # print(installs['video'])
        installs = uniconf.installs
        self.camera_height = installs['video']['height']

        self.x_limits = [-200, 200]
        self.y_limits = [-15, 15]
        self.ipm_width = 480
        self.ipm_height = 1440
        self.ipm_front_height = int(self.ipm_height/2)
        self.intrinsic_para = {"video": np.array(((installs['video']['fu'], 0, installs['video']['cu']), (0, installs['video']['fv'], installs['video']['cv']), (0, 0, 1)))}
        self.r_cam2img = np.array(((0, 1, 0), (0, 0, 1), (1, 0, 0)))
        self.yaw = installs['video']['yaw']
        self.pitch = installs['video']['pitch']
        self.roll = installs['video']['roll']
        self.m_R_w2i = {
            "video": self.calc_m_w2i(installs['video'].get('yaw', 0), installs['video'].get("pitch", 0), installs['video'].get("roll", 0))
        }
        self.cfg = uniconf
        self.cfg.installs['default'] = {'lat_offset': 0.0, 'lon_offset': 0.0, 'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}

    def calc_m_w2i(self, y, p, r, install_key="video"):
        # self.yaw = y
        # self.pitch = p
        # self.roll = r
        if self.intrinsic_para.get(install_key) is None:
            installs = self.cfg.installs
            self.intrinsic_para[install_key] = np.array(((installs[install_key]['fu'], 0, installs[install_key]['cu']), (0, installs[install_key]['fv'], installs[install_key]['cv']), (0, 0, 1)))
        yaw = y * pi / 180      # Z?????????
        pitch = p * pi / 180    # Y?????????
        roll = r * pi / 180     # X?????????

        c_roll = cos(roll)
        s_roll = sin(roll)
        r_roll = np.array(((1, 0, 0),
                           (0, c_roll, s_roll),
                           (0, -s_roll, c_roll)))

        c_pitch = cos(pitch)
        s_pitch = sin(pitch)
        r_pitch = np.array(((c_pitch, 0, -s_pitch),
                            (0, 1, 0),
                            (s_pitch, 0, c_pitch)))

        c_yaw = cos(yaw)
        s_yaw = sin(yaw)
        r_yaw = np.array(((c_yaw, s_yaw, 0),
                          (-s_yaw, c_yaw, 0),
                          (0, 0, 1)))

        r_att = np.dot(r_roll, np.dot(r_pitch, r_yaw))

        vector = np.dot(self.r_cam2img, r_att)     # ????????????
        return np.dot(self.intrinsic_para[install_key], vector)     # ?????????????????????

    def update_m_r2i(self, y, p, r, install_key="video"):
        self.m_R_w2i[install_key] = self.calc_m_w2i(self.yaw+y, self.pitch+p, self.roll+r)

    def getp_ifc_from_poly(self, coefs, step=0.1, start=0, end=60, sensor=None):
        a0, a1, a2, a3 = coefs
        p = []
        if step <= 0:
            # print('ivalid step', step)
            return
        x = np.arange(start, end, step)
        y = a0 + a1 * x + a2 * np.power(x, 2) + a3 * np.power(x, 3)
        for i, item in enumerate(x):
            u, v = self.compensate_param_rcs(x[i], y[i], sensor)
            tx, ty = self.trans_gnd2raw(u, v)
            p.append((int(tx), int(ty)))
        return p

        # for x in np.arange(start, end, step):
        #     y = a0 + a1 * x + a2 * x ** 2 + a3 * x ** 3
        #     if sensor:
        #         x, y = self.compensate_param_rcs(x, y, sensor)
        #     tx, ty = self.trans_gnd2raw(x, y)
        #     p.append((int(tx), int(ty)))
        # return p

    def getp_ipm_from_poly(self, coefs, step=0.1, start=0, end=60, sensor=None):
        a0, a1, a2, a3 = coefs
        p = []

        x = np.arange(start, end, step)
        y = a0 + a1 * x + a2 * np.power(x, 2) + a3 * np.power(x, 3)
        for i, item in enumerate(x):
            u, v = self.compensate_param_rcs(x[i], y[i], sensor)
            tx, ty = self.trans_gnd2ipm(u, v)
            p.append((int(tx), int(ty)))
        return p

        # for x in np.arange(start, end, step):
        #     y = a0 + a1 * x + a2 * x ** 2 + a3 * x ** 3
        #     if sensor:
        #         x, y = self.compensate_param_rcs(x, y, sensor)
        #     tx, ty = self.trans_gnd2ipm(x, y)
        #     p.append((int(tx), int(ty)))
        # return p

    def getp_gnd_from_poly(self, coefs, r=60, step=0.1, dev='ifv300'):
        a0, a1, a2, a3 = coefs
        p = []

        for x in np.arange(0, r, step):
            y = a0 + a1 * x + a2 * x ** 2 + a3 * x ** 3
            xg = x + self.cfg.installs[dev]['lon_offset']
            yg = y + self.cfg.installs[dev]['lat_offset']
            p.append((xg, yg))
        return p

    def trans_gnd2raw(self, x, y, h=None, install_key="video", filter_back=True):
        if h is None:
            h = 0

        if self.m_R_w2i.get(install_key) is None and self.cfg.installs.get(install_key):
            self.m_R_w2i[install_key] = self.calc_m_w2i(
                self.cfg.installs[install_key].get('yaw', 0),
                self.cfg.installs[install_key].get('pitch', 0),
                self.cfg.installs[install_key].get('roll', 0),
                install_key=install_key)

        # ????????????
        h1 = self.cfg.installs[install_key]['height'] - h
        x = x - self.cfg.installs[install_key]['lon_offset']
        y = y - self.cfg.installs[install_key]['lat_offset']

        # ???????????????
        r = self.cfg.installs[install_key].get('ref_yaw', 0) * pi / 180
        x = x*cos(r) + y*sin(r)
        y = y*cos(r) - x*sin(r)

        if filter_back and x < 0:
            return

        p_xyz = np.array([x, y, h1])

        vector = self.m_R_w2i[install_key]
        uv_t = np.dot(vector, p_xyz)
        try:
            uv_new = uv_t / uv_t[2]
            x, y = int(uv_new[0]), int(uv_new[1])
            return x, y
        except Exception as e:
            print(e)
            print(f"h:{h} self.camera_height:{self.camera_height}")
            print(f"??????????????????uv_new = uv_t / uv_t[2] uv_t:{uv_t} uv_t[2]:{uv_t[2]} x:{x} y:{y}")
            print(f"self.cfg.installs['video']:{self.cfg.installs[install_key]}")

    def trans_gnd2ipm(self, x, y, dev='ifv300'):
        x_scale = self.ipm_height / (self.x_limits[1] - self.x_limits[0])
        y_scale = self.ipm_width / (self.y_limits[1] - self.y_limits[0])
        x += self.cfg.installs[dev]['lon_offset']
        y += self.cfg.installs[dev]['lat_offset']
        ipm_y = (-x + self.x_limits[1]) * x_scale
        ipm_x = (y - self.y_limits[0]) * y_scale
        return int(ipm_x), int(ipm_y)

    def trans_polar2rcs(self, angle, range, sensor):
        param = self.cfg.installs.get(sensor)
        if not param:
            source = sensor.split('.')
            source = source[3] if len(source) > 2 else source[0]
            param = self.cfg.installs.get(source)
        if not param:
            x = cos(angle * pi / 180.0) * range
            y = sin(angle * pi / 180.0) * range
        else:
            angle = angle - param['yaw']
            x = cos(angle * pi / 180.0) * range + param['lon_offset']
            y = sin(angle * pi / 180.0) * range + param['lat_offset']
        return x, y

    def compensate_param_rcs(self, x, y, sensor):
        range, angle = self.trans_rcs2polar(x, y)
        return self.trans_polar2rcs(angle, range, sensor)

    def trans_rcs2polar(self, x, y):
        """
        ??????x???y????????????????????????0.0?????????????????????
        :param x:
        :param y:
        :return:
        """
        range = sqrt(x ** 2 + y ** 2)
        angle = atan2(y, x) * 180 / pi
        return range, angle

    def calc_g2i_matrix(self):
        p0 = self.trans_gnd2raw(self.x_limits[1], self.y_limits[0], filter_back=False)
        p1 = self.trans_gnd2raw(self.x_limits[1], self.y_limits[1], filter_back=False)
        p2 = self.trans_gnd2raw(self.x_limits[0], self.y_limits[1], filter_back=False)
        p3 = self.trans_gnd2raw(self.x_limits[0], self.y_limits[0], filter_back=False)
        src = np.array([p0, p1, p2, p3], np.float32)
        dst = np.array([[0, 0], [self.ipm_width - 1, 0], [self.ipm_width - 1, self.ipm_height - 1],
                        [0, self.ipm_height - 1]], np.float32)
        m_g2i = cv2.getPerspectiveTransform(src, dst)
        return m_g2i

    def rmse(self, predictions, targets):
        if isinstance(predictions, list):
            p = np.array(predictions)
        else:
            p = predictions
        if isinstance(targets, list):
            t = np.array(targets)
        else:
            t = targets
        return np.sqrt(((p - t) ** 2).mean())


def prep_replay(source):
    """
    ?????????????????????????????????????????????
    :param source:
    :param ns:
    :param chmain:
    :return:
    """
    # ??????????????????
    config_path = os.path.join(os.path.dirname(source), 'config.json')
    install_path = os.path.join(os.path.dirname(source), 'installation.json')
    uniconf = CVECfg()
    if os.path.exists(config_path):
        print("use config:", config_path)
        uniconf.configs = json.load(open(config_path))
    if os.path.exists(install_path):
        print("install:", install_path)
        uniconf.installs = json.load(open(install_path))

    return uniconf


if __name__ == '__main__':
    pass
    uiconfig = prep_replay("/home/mini/work/20211111154044/log.txt")
    t = Transform(uniconf=uiconfig)
    x1, y1 = t.trans_gnd2raw(-28.21, 0.13, install_key="a1j_algo.12")
    print("x1", x1, "y1", y1)
    # x2, y2 = t.trans_gnd2raw(80.6000000000000223, 13.800000000000011, install_key='cv22_algo.12')
    # print("x2", x2, "y2", y2)

# a1j_algo.12 id:16   x:-28.21   y:0.13     x0:954.00   y0:428.00   height:1080 width:1920
# a1j_algo.12 id:13   x:-24.84   y:-4.13    x0:1216.00  y0:416.00   height:1080 width:1920
# a1j_algo.12 id:8    x:-40.90   y:-3.38    x0:1080.00  y0:455.00   height:1080 width:1920
# a1j_algo.12 id:9    x:-41.71   y:-3.43    x0:1079.00  y0:456.00   height:1080 width:1920
# a1j_algo.12 id:17   x:-4.84    y:-3.94    x0:6588.00  y0:-1563.00 height:1080 width:1920
# a1j_algo.12 id:6    x:-33.71   y:-3.62    x0:1118.00  y0:443.00   height:1080 width:1920
# a1j_algo.12 id:18   x:-52.84   y:-2.88    x0:1038.00  y0:467.00   height:1080 width:1920
# a1j_algo.12 id:15   x:-61.09   y:-4.60    x0:1065.00  y0:473.00   height:1080 width:1920
# a1j_algo.12 id:1    x:-55.09   y:-13.07   x0:1290.00  y0:469.00   height:1080 width:1920
