#!/usr/bin/env python
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

    def update_r2i(self):
        self.transform.update_m_r2i(self.cfg.installs['video']['yaw'], self.cfg.installs['video']['pitch'],
                                    self.cfg.installs['video']['roll'])
        print('current yaw:{} pitch:{} roll:{}'.format(self.cfg.installs['video']['yaw'],
                                                       self.cfg.installs['video']['pitch'],
                                                       self.cfg.installs['video']['roll']))

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
        fu = installs['video']['fu']
        fv = installs['video']['fv']
        cu = installs['video']['cu']
        cv = installs['video']['cv']

        self.x_limits = [0.01, 180]
        self.y_limits = [-15, 15]
        self.ipm_width = 480
        self.ipm_height = 720
        self.intrinsic_para = np.array(((fu, 0, cu), (0, fv, cv), (0, 0, 1)))
        self.r_cam2img = np.array(((0, 1, 0), (0, 0, 1), (1, 0, 0)))
        self.m_R_w2i = self.calc_m_w2i(installs['video']['yaw'], installs['video']['pitch'], installs['video']['roll'])
        self.cfg = uniconf
        self.cfg.installs['default'] = {'lat_offset': 0.0, 'lon_offset': 0.0, 'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}

    def calc_m_w2i(self, y, p, r):
        yaw = y * pi / 180
        pitch = p * pi / 180
        roll = r * pi / 180
        r_roll = np.array(((1, 0, 0),
                           (0, cos(roll), sin(roll)),
                           (0, -sin(roll), cos(roll))))

        r_pitch = np.array(((cos(pitch), 0, -sin(pitch)),
                            (0, 1, 0),
                            (sin(pitch), 0, cos(pitch))))

        r_yaw = np.array(((cos(yaw), sin(yaw), 0),
                          (-sin(yaw), cos(yaw), 0),
                          (0, 0, 1)))

        r_att = np.dot(r_roll, np.dot(r_pitch, r_yaw))

        return np.dot(self.intrinsic_para, np.dot(self.r_cam2img, r_att))

    def update_m_r2i(self, y, p, r):
        self.m_R_w2i = self.calc_m_w2i(y, p, r)

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

    def trans_gnd2raw(self, x, y, h=None):
        if h is None:
            h = 0
        h1 = self.camera_height - h
        # x = x - self.cfg.installs['video']['lon_offset'] + self.cfg.installs[dev]['lon_offset']
        # y = y - self.cfg.installs['video']['lat_offset'] + self.cfg.installs[dev]['lat_offset']
        x = x - self.cfg.installs['video']['lon_offset']
        y = y - self.cfg.installs['video']['lat_offset']
        p_xyz = np.array([x, y, h1])
        uv_t = np.dot(self.m_R_w2i, p_xyz)
        uv_new = uv_t / uv_t[2]
        # if uv_new[0] > 10000:
        #     uv_new[0] = 10000
        # if uv_new[1] > 10000:
        #     uv_new[1] = 10000
        return int(uv_new[0]), int(uv_new[1])

    def transf_gnd2raw(self, x, y, h=None):
        if h is None:
            h = 0
        # x = x - self.cfg.installs['video']['lon_offset'] + self.cfg.installs[dev]['lon_offset']
        # y = y - self.cfg.installs['video']['lat_offset'] + self.cfg.installs[dev]['lat_offset']
        x = x - self.cfg.installs['video']['lon_offset']
        y = y - self.cfg.installs['video']['lat_offset']
        p_xyz = np.array([x, y, self.camera_height - h])
        uv_t = np.dot(self.m_R_w2i, p_xyz)
        uv_new = uv_t / uv_t[2]
        return uv_new[0], uv_new[1]

    def trans_gnd2ipm(self, x, y, dev='ifv300'):
        x_scale = self.ipm_height / (self.x_limits[1] - self.x_limits[0])
        y_scale = self.ipm_width / (self.y_limits[1] - self.y_limits[0])
        x += self.cfg.installs[dev]['lon_offset']
        y += self.cfg.installs[dev]['lat_offset']
        ipm_y = (-x + self.x_limits[1]) * x_scale
        ipm_x = (y - self.y_limits[0]) * y_scale
        return int(ipm_x), int(ipm_y)

    def transf_gnd2ipm(self, x, y, dev='ifv300'):
        x_scale = self.ipm_height / (self.x_limits[1] - self.x_limits[0])
        y_scale = self.ipm_width / (self.y_limits[1] - self.y_limits[0])
        x += self.cfg.installs[dev]['lon_offset']
        y += self.cfg.installs[dev]['lat_offset']
        ipm_y = (-x + self.x_limits[1]) * x_scale
        ipm_x = (y - self.y_limits[0]) * y_scale
        return ipm_x, ipm_y

    def trans_polar2rcs(self, angle, range, sensor):
        param = self.cfg.installs.get(sensor)
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
        range = sqrt(x ** 2 + y ** 2)
        angle = atan2(y, x) * 180 / pi
        return range, angle

    def calc_g2i_matrix(self):
        p0 = self.trans_gnd2raw(self.x_limits[1], self.y_limits[0])
        p1 = self.trans_gnd2raw(self.x_limits[1], self.y_limits[1])
        p2 = self.trans_gnd2raw(self.x_limits[0], self.y_limits[1])
        p3 = self.trans_gnd2raw(self.x_limits[0], self.y_limits[0])
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

    def iter_yaw(self, x, y, h, vx, vy, step=0.01, dataroot='etc/'):
        max_iter = 10
        thres_dx = 2
        dx = 9999
        while max_iter > 0:
            vx1, vy1 = self.transf_gnd2raw(x, y, h)
            dx = vx1 - vx
            if dx < thres_dx:
                break
            d_yaw = step * dx
            self.cfg.installs['video']['yaw'] = self.cfg.installs['video']['yaw'] + d_yaw
            self.update_m_r2i(self.cfg.installs['video']['yaw'], self.cfg.installs['video']['pitch'],
                              self.cfg.installs['video']['roll'])
            max_iter -= 1

        if dx < thres_dx:
            print('yaw calibration succeeded.', dx)
            print('yaw:', self.cfg.installs['video']['yaw'])
            json.dump(self.cfg.installs, open(os.path.join(dataroot, 'instl_cal.json')), indent=True)
        else:
            print('yaw calibration failed.', dx)


if __name__ == '__main__':
    pass
    # import os
    # os.chdir(os.path.join('../', os.path.dirname(os.path.dirname(__file__))))
    # print(os.getcwd())
    # from config.config import install
    # a = Transform()
    # b = Transform()
    # print(id(a), id(b))
