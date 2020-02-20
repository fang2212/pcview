#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2019/04/02
# @Author  : simon.xu
# @File    : vehicle.py
# @Desc    :

from collections import deque
# from itertools import combinations
from math import *

from tools.geo import *


class Vehicle(object):
    def __init__(self, tag, mass=1530, width=1.865, length=4.861, height=1.489, wheelbase=2.841):
        self.tag = tag
        self.source = None
        self.mass = mass
        self.width = width
        self.length = length
        self.height = height
        self.wheelbase = wheelbase
        self.dynamics = {'pitch': deque(maxlen=20),
                         'yaw': deque(maxlen=20),
                         'roll': deque(maxlen=20),
                         'lat': deque(maxlen=20),
                         'lon': deque(maxlen=20),
                         'hgt': deque(maxlen=20),
                         'velN': deque(maxlen=20),
                         'velE': deque(maxlen=20),
                         'velD': deque(maxlen=20),
                         'ax': deque(maxlen=20),
                         'ay': deque(maxlen=20),
                         'az': deque(maxlen=20),
                         'yaw_rate': deque(maxlen=20),
                         'speed': deque(maxlen=20),
                         'hor_speed': deque(maxlen=20),
                         'vert_speed': deque(maxlen=20),
                         'trk_gnd': deque(maxlen=20),
                         # 'pinpoint': deque(maxlen=20),
                         'road_grad_x': deque(maxlen=20)}
        self.pinpoint = None
        # self.road_gradient = 0.0
        # self.pitch_history = deque(maxlen=100)
        # self.pitch_history.append(0.0)
        # self.pitch_history.append(0.0)
        # self.pitch_history.append(0.0)

    def update_dynamics(self, dyn):
        self.source = dyn['source']
        if dyn['type'] == 'pinpoint':
            self.set_pinpoint(dyn)
        if dyn['type'] not in ['bestpos', 'bestvel', 'heading', 'vehicle_state']:
            return

        for key in self.dynamics:
            if key in dyn:
                # self.dynamics[key][0] = dyn[key]
                ts = dyn.get('ts_origin') or dyn['ts']
                # self.dynamics[key][1] = ts if ts else dyn['ts']
                self.dynamics[key].appendleft((ts, dyn[key]))

                # if key == 'pitch':
                #     self.pitch_history.append(dyn[key])
                #     self.road_gradient = np.mean(self.pitch_history)
                # self.dynamics[key][0] = np.mean(list(self.pitch_history)[-3:-1])
        # print(self.dynamics['pinpoint'])

    def set_pinpoint(self, pp):
        self.pinpoint = pp

    def get_pos(self, ts=None):
        for idx0, pitch in enumerate(self.dynamics['pitch']):
            ts0 = pitch[0]
            for idx1, lat in enumerate(self.dynamics['lat']):
                ts1 = lat[0]
                if ts0 == ts1:
                    if (ts and ts == ts0) or not ts:
                        return {
                            'ts': lat[0],
                            'lat': self.dynamics['lat'][idx1][1],
                            'lon': self.dynamics['lon'][idx1][1],
                            'hgt': self.dynamics['hgt'][idx1][1],
                            'pitch': self.dynamics['pitch'][idx0][1],
                            'yaw': self.dynamics['yaw'][idx0][1]
                        }
                if ts1 <= ts0:
                    break
            if ts and ts0 <= ts:
                return
        # tss = [self.dynamics[key][1] for key in self.dynamics]
        # ts_max = max(tss)

    def get_dynamics(self, items, ts=None):
        r = {'source': self.source}

        for val0 in self.dynamics[items[0]]:
            for item in items[1:]:
                if len(self.dynamics[item]) == 0:
                    return
                for val1 in self.dynamics[item]:
                    if val1[0] == val0[0]:
                        # print(val0, val1)
                        r[items[0]] = val0[1]
                        r[item] = val1[1]
                        r['ts'] = val0[0]
                        break

                    if val1[0] < val0[0]:
                        return

            return r
        # if not fail:
        #     return r

    def get_pp_target(self):
        if not self.pinpoint:
            return
        host = self.get_dynamics(('lat', 'lon', 'hgt', 'pitch', 'yaw', 'hor_speed', 'trk_gnd'))
        # print(host)
        pp = self.pinpoint
        # print('get pp target', self.pinpoint, host)
        if not host or not pp:
            return
        if 'yaw' not in host or 'lat' not in host or 'lon' not in host:
            return
        # print('get pp target')
        range = gps_distance(pp['lat'], pp['lon'], host['lat'], host['lon'])
        angle = gps_bearing(pp['lat'], pp['lon'], host['lat'], host['lon'])
        angle = angle - host['yaw']

        trk_host = host['trk_gnd'] + 180.0
        if trk_host > 360:
            trk_host = trk_host - 360.0
        velN = - host['hor_speed'] * cos(host['trk_gnd'] * pi / 180.0)
        velE = - host['hor_speed'] * sin(host['trk_gnd'] * pi / 180.0)
        # vel_x = host['hor_speed'] * sin(trk_host * pi / 180)
        # vel_y = host['hor_speed'] * cos(trk_host * pi / 180)
        theta = host['trk_gnd'] - host['yaw']
        vel_x = host['hor_speed'] * cos(theta * pi / 180)
        vel_y = host['hor_speed'] * sin(theta * pi / 180)
        pos_x = cos(angle * pi / 180.0) * range
        pos_y = sin(angle * pi / 180.0) * range
        delta_h = host['hgt'] - pp['hgt']

        ttc = pos_x / host['hor_speed'] if host['hor_speed'] > 0 else 7
        if ttc > 7:
            ttc = 7

        return {'ts': host['ts'], 'source': self.source, 'type': 'rtktarget', 'range': range, 'angle': angle,
                'delta_hgt': delta_h, 'pos_lat': pos_y, 'pos_lon': pos_x, 'vel_lat': vel_y, 'vel_lon': vel_x,
                'TTC': ttc}


def get_vehicle_target(host, target):
    host_dyn = host.get_dynamics(('lat', 'lon', 'hgt', 'pitch', 'yaw', 'hor_speed', 'trk_gnd'))
    target_dyn = target.get_dynamics(('lat', 'lon', 'hgt', 'hor_speed', 'trk_gnd'))
    if not host_dyn or not target_dyn:
        return

    range = gps_distance(target_dyn['lat'], target_dyn['lon'], host_dyn['lat'], host_dyn['lon'])
    angle = gps_bearing(target_dyn['lat'], target_dyn['lon'], host_dyn['lat'], host_dyn['lon'])
    angle = angle - host_dyn['yaw']
    velN = target_dyn['hor_speed']*cos(target_dyn['trk_gnd'] * pi / 180.0) - host_dyn['hor_speed']*cos(host_dyn['trk_gnd'] * pi / 180.0)
    velE = target_dyn['hor_speed']*sin(target_dyn['trk_gnd'] * pi / 180.0) - host_dyn['hor_speed']*sin(host_dyn['trk_gnd'] * pi / 180.0)
    trk = atan2(velE, velN) * 180.0 / pi
    if trk < 0:
        trk = trk + 360.0
    vel = (velE**2 + velN**2)**0.5
    vel_x = vel * sin(trk * pi / 180)
    vel_y = vel * cos(trk * pi / 180)
    pos_x = cos(angle * pi / 180.0) * range
    pos_y = sin(angle * pi / 180.0) * range
    delta_h = host_dyn['hgt'] - target_dyn['hgt']

    return {'ts': host['ts'], 'source': target['source'], 'type': 'rtktarget', 'range': range, 'angle': angle,
            'delta_hgt': delta_h, 'pos_lat': pos_y, 'pos_lon': pos_x, 'vel_lat': vel_y, 'vel_lon': vel_x,
            'TTC': pos_x / vel_x}
