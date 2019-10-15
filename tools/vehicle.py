#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2019/04/02
# @Author  : simon.xu
# @File    : vehicle.py
# @Desc    :

from collections import deque
import numpy as np


class Vehicle(object):
    def __init__(self, mass=1530, width=1.865, length=4.861, height=1.489, wheelbase=2.841):
        self.mass = mass
        self.width = width
        self.length = length
        self.height = height
        self.wheelbase = wheelbase
        self.dynamics = {'pitch': [0.0, 0.0],
                         'yaw': [0.0, 0.0],
                         'roll': [0.0, 0.0],
                         'lat': [0.0, 0.0],
                         'lon': [0.0, 0.0],
                         'hgt': [0.0, 0.0],
                         'velN': [0.0, 0.0],
                         'velE': [0.0, 0.0],
                         'velD': [0.0, 0.0],
                         'yaw_rate': [0.0, 0.0],
                         'speed': [0.0, 0.0],
                         'pinpoint': None}
        self.road_gradient = 0.0
        self.pitch_history = deque(maxlen=100)
        self.pitch_history.append(0.0)
        self.pitch_history.append(0.0)
        self.pitch_history.append(0.0)

    def update_dynamics(self, dyn):
        for key in self.dynamics:
            if key in dyn:
                self.dynamics[key][0] = dyn[key]
                ts = dyn.get('ts_origin')
                self.dynamics[key][1] = ts if ts else dyn['ts']
                if key == 'pitch':
                    self.pitch_history.append(dyn[key])
                    self.road_gradient = np.mean(self.pitch_history)
                    # self.dynamics[key][0] = np.mean(list(self.pitch_history)[-3:-1])


