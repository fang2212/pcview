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
from math import sin, cos, pi, atan2
import cv2
import numpy as np
from config.config import install


class Transform:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.camera_height = install['video']['height']
        fu = install['video']['fu']
        fv = install['video']['fv']
        cu = install['video']['cu']
        cv = install['video']['cv']

        self.x_limits = [0, 180]
        self.y_limits = [-15, 15]
        self.ipm_width = 480
        self.ipm_height = 720
        self.intrinsic_para = np.array(((fu, 0, cu), (0, fv, cv), (0, 0, 1)))
        self.r_cam2img = np.array(((0, 1, 0), (0, 0, 1), (1, 0, 0)))
        self.m_R_w2i = self.calc_m_w2i(install['video']['yaw'], install['video']['pitch'], install['video']['roll'])

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

    def trans_gnd2raw(self, x, y, h=None):
        if h is None:
            h = self.camera_height
        x = x - install['video']['lon_offset']
        y = y - install['video']['lat_offset']
        p_xyz = np.array([x, y, h])
        uv_t = np.dot(self.m_R_w2i, p_xyz)
        uv_new = uv_t / uv_t[2]

        return int(uv_new[0]), int(uv_new[1])

    def transf_gnd2raw(self, x, y, h=None):
        if h is None:
            h = self.camera_height
        x = x - install['video']['lon_offset']
        y = y - install['video']['lat_offset']
        p_xyz = np.array([x, y, h])
        uv_t = np.dot(self.m_R_w2i, p_xyz)
        uv_new = uv_t / uv_t[2]
        return uv_new[0], uv_new[1]

    def trans_gnd2ipm(self, x, y):
        x_scale = self.ipm_height / (self.x_limits[1] - self.x_limits[0])
        y_scale = self.ipm_width / (self.y_limits[1] - self.y_limits[0])

        ipm_y = (-x + self.x_limits[1]) * x_scale
        ipm_x = (y - self.y_limits[0]) * y_scale
        return int(ipm_x), int(ipm_y)

    def transf_gnd2ipm(self, x, y):
        x_scale = self.ipm_height / (self.x_limits[1] - self.x_limits[0])
        y_scale = self.ipm_width / (self.y_limits[1] - self.y_limits[0])

        ipm_y = (-x + self.x_limits[1]) * x_scale
        ipm_x = (y - self.y_limits[0]) * y_scale
        return ipm_x, ipm_y

    def trans_polar2rcs(self, angle, range, param=None):
        if not param:
            x = cos(angle * pi / 180.0) * range
            y = sin(angle * pi / 180.0) * range
        else:
            angle = angle - param['yaw']
            x = cos(angle * pi / 180.0) * range + param['lon_offset']
            y = sin(angle * pi / 180.0) * range + param['lat_offset']
        return x, y

    def compensate_param(self, data, param):
        if 'pos_lat' in data and 'pos_lon' in data:
            data['pos_lon'] = data['pos_lon'] + param['lon_offset']
            data['pos_lat'] = data['pos_lat'] + param['lat_offset']

    def trans_rcs2polar(self, x, y):
        range = (x ** 2 + y ** 2) ** 0.5
        angle = atan2(y, x)
        return range, angle

    def calc_g2i_matrix(self):
        p0 = self.trans_gnd2raw(self.x_limits[1], self.y_limits[0])
        p1 = self.trans_gnd2raw(self.x_limits[1], self.y_limits[1])
        p2 = self.trans_gnd2raw(self.x_limits[0], self.y_limits[1])
        p3 = self.trans_gnd2raw(self.x_limits[0], self.y_limits[0])
        src = np.array([p0, p1, p2, p3], np.float32)
        dst = np.array([[0, 0], [self.ipm_width - 1, 0], [self.ipm_width - 1, self.ipm_height - 1],
                        [0, self.ipm_height-1]], np.float32)
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
            install['video']['yaw'] = install['video']['yaw'] + d_yaw
            self.update_m_r2i(install['video']['yaw'], install['video']['pitch'], install['video']['roll'])
            max_iter -= 1

        if dx < thres_dx:
            print('yaw calibration succeeded.', dx)
            print('yaw:', install['video']['yaw'])
            json.dump(install, open(os.path.join(dataroot, 'instl_cal.json')), indent=True)
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
