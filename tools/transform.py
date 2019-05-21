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

camera_height = install['video']['height']
fu = install['video']['fu']
fv = install['video']['fv']
cu = install['video']['cu']
cv = install['video']['cv']

x_limits = [0, 180]
y_limits = [-15, 15]
ipm_width = 480
ipm_height = 720

intrinsic_para = np.array(((fu, 0, cu),
                           (0, fv, cv),
                           (0, 0, 1)))

r_cam2img = np.array(((0, 1, 0),
                      (0, 0, 1),
                      (1, 0, 0)))


def calc_m_w2i(y, p, r):
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

    return np.dot(intrinsic_para, np.dot(r_cam2img, r_att))


m_R_w2i = calc_m_w2i(install['video']['yaw'], install['video']['pitch'], install['video']['roll'])


def update_m_r2i(y, p, r):
    global m_R_w2i
    m_R_w2i = calc_m_w2i(y, p, r)


def trans_gnd2raw(x, y, h=camera_height):
    # m_R_w2i = calc_m_w2i(install['video']['yaw'], install['video']['pitch'], install['video']['roll'])
    x = x - install['video']['lon_offset']
    y = y - install['video']['lat_offset']
    p_xyz = np.array([x, y, h])
    uv_t = np.dot(m_R_w2i, p_xyz)
    uv_new = uv_t / uv_t[2]

    return int(uv_new[0]), int(uv_new[1])


def transf_gnd2raw(x, y, h=camera_height):
    # m_R_w2i = calc_m_w2i(install['video']['yaw'], install['video']['pitch'], install['video']['roll'])
    x = x - install['video']['lon_offset']
    y = y - install['video']['lat_offset']
    p_xyz = np.array([x, y, h])
    uv_t = np.dot(m_R_w2i, p_xyz)
    uv_new = uv_t / uv_t[2]

    return uv_new[0], uv_new[1]


def trans_gnd2ipm(x, y):
    x_scale = ipm_height / (x_limits[1] - x_limits[0])
    y_scale = ipm_width / (y_limits[1] - y_limits[0])

    ipm_y = (-x + x_limits[1]) * x_scale
    ipm_x = (y - y_limits[0]) * y_scale

    return int(ipm_x), int(ipm_y)


def transf_gnd2ipm(x, y):
    x_scale = ipm_height / (x_limits[1] - x_limits[0])
    y_scale = ipm_width / (y_limits[1] - y_limits[0])

    ipm_y = (-x + x_limits[1]) * x_scale
    ipm_x = (y - y_limits[0]) * y_scale

    return ipm_x, ipm_y


def trans_polar2rcs(angle, range, param=None):
    if not param:
        x = cos(angle * pi / 180.0) * range
        y = sin(angle * pi / 180.0) * range
    else:
        angle = angle - param['yaw']
        x = cos(angle * pi / 180.0) * range + param['lon_offset']
        y = sin(angle * pi / 180.0) * range + param['lat_offset']

    return x, y


def compensate_param(data, param):
    if 'pos_lat' in data and 'pos_lon' in data:
        data['pos_lon'] = data['pos_lon'] + param['lon_offset']
        data['pos_lat'] = data['pos_lat'] + param['lat_offset']


def trans_rcs2polar(x, y):
    range = (x ** 2 + y ** 2) ** 0.5
    angle = atan2(y, x)

    return range, angle


def calc_g2i_matrix():
    p0 = trans_gnd2raw(x_limits[1], y_limits[0])
    p1 = trans_gnd2raw(x_limits[1], y_limits[1])
    p2 = trans_gnd2raw(x_limits[0], y_limits[1])
    p3 = trans_gnd2raw(x_limits[0], y_limits[0])
    # print(p0, p1, p2, p3)
    src = np.array([p0, p1, p2, p3], np.float32)
    dst = np.array([[0, 0], [ipm_width - 1, 0], [ipm_width - 1, ipm_height - 1], [0, ipm_height - 1]], np.float32)
    m_g2i = cv2.getPerspectiveTransform(src, dst)
    # print('m_g2i:\n', m_g2i)
    return m_g2i


def rmse(predictions, targets):
    if isinstance(predictions, list):
        p = np.array(predictions)
    else:
        p = predictions
    if isinstance(targets, list):
        t = np.array(targets)
    else:
        t = targets

    return np.sqrt(((p - t) ** 2).mean())


def iter_yaw(x, y, h, vx, vy, step=0.01, dataroot='etc/'):
    max_iter = 10
    thres_dx = 2
    dx = 9999
    while max_iter > 0:
        vx1, vy1 = transf_gnd2raw(x, y, h)
        dx = vx1 - vx
        if dx < thres_dx:
            break
        d_yaw = step * dx
        install['video']['yaw'] = install['video']['yaw'] + d_yaw
        update_m_r2i(install['video']['yaw'], install['video']['pitch'], install['video']['roll'])
        max_iter -= 1

    if dx < thres_dx:
        print('yaw calibration succeeded.', dx)
        print('yaw:', install['video']['yaw'])
        json.dump(install, open(os.path.join(dataroot, 'instl_cal.json')), indent=True)
    else:
        print('yaw calibration failed.', dx)
