import numpy as np
from math import *
from config.config import install
import cv2

pitch = install['video']['pitch'] * pi / 180
yaw = install['video']['yaw'] * pi / 180
roll = install['video']['roll'] * pi / 180
camera_height = install['video']['height']
fu = install['video']['fu']
fv = install['video']['fv']
cu = install['video']['cu']
cv = install['video']['cv']

x_limits = [5, 180]
y_limits = [-15, 15]
ipm_width = 480
ipm_height = 720

intrinsic_para = np.array(((fu, 0, cu),
                           (0, fv, cv),
                           (0, 0, 1)))

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
r_cam2img = np.array(((0, 1, 0),
                      (0, 0, 1),
                      (1, 0, 0)))

m_R_w2i = np.dot(intrinsic_para, np.dot(r_cam2img, r_att))


def trans_gnd2raw(x, y):
    x = x - install['video']['lon_offset']
    y = y - install['video']['lat_offset']
    p_xyz = np.array([x, y, camera_height])
    uv_t = np.dot(m_R_w2i, p_xyz)
    uv_new = uv_t / uv_t[2]

    return int(uv_new[0]), int(uv_new[1])


def trans_gnd2ipm(x, y):
    x_scale = ipm_height / (x_limits[1] - x_limits[0])
    y_scale = ipm_width / (y_limits[1] - y_limits[0])

    ipm_y = (-x + x_limits[1]) * x_scale
    ipm_x = (y - y_limits[0]) * y_scale

    return int(ipm_x), int(ipm_y)


def trans_polar2rcs(angle, range, param=None):
    if not param:
        x = cos(angle * pi / 180.0) * range
        y = sin(angle * pi / 180.0) * range
    else:
        angle = angle - param['yaw']
        x = cos(angle * pi / 180.0) * range + param['lon_offset']
        y = sin(angle * pi / 180.0) * range - param['lat_offset']

    return x, y


def trans_rcs2polar(x, y):
    range = (x**2 + y**2)**0.5
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


def convert(data):
    '''
    msgpack dict type value convert
    delete b'
    '''
    if isinstance(data, bytes):      return data.decode('ascii')
    if isinstance(data, dict):       return dict(map(convert, data.items()))
    if isinstance(data, tuple):      return tuple(map(convert, data))
    if isinstance(data, list):       return list(map(convert, data))
    if isinstance(data, set):        return set(map(convert, data))
    return data

