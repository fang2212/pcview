#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file    :   rt_range.py    
@contact :   caofulin@minieye.cc
@date    :   2021/3/10 下午4:45
"""

import cantools
db_rt = cantools.database.load_file('dbc/RT-Range_User.dbc', strict=False)


def parser_rt(id, buf, ctx=None):

    ids = [m.frame_id for m in db_rt.messages]
    if id not in ids:
        return None

    r = db_rt.decode_message(id, buf, decode_choices=False)

    """
    BO_ 1968 Range1Forward: 8 RTRange
     SG_ Range1PosForward : 0|32@1- (0.001,0) [-2147483.6475|2147483.6475] "m" Vector__XXX
     SG_ Range1VelForward : 32|16@1- (0.01,0) [-327.675|327.675] "m/s" Vector__XXX
     SG_ Range1TimeToCollisionForward : 48|16@1- (0.001,0) [-32.7675|32.7675] "s" Vector__XXX
    
    BO_ 1969 Range1Lateral: 8 RTRange
     SG_ Range1PosLateral : 0|32@1- (0.001,0) [-2147483.6475|2147483.6475] "m" Vector__XXX
     SG_ Range1VelLateral : 32|16@1- (0.01,0) [-327.675|327.675] "m/s" Vector__XXX
     SG_ Range1TimeToCollisionLateral : 48|16@1- (0.001,0) [-32.7675|32.7675] "s" Vector__XXX
    
    """

    if id == 1968:
        obs = {'type': 'obstacle', 'sensor': 'rt', "pos_lon": r['Range1PosForward'], "id": 1, 'cipo': 1,
               'vel_lon': r['Range1VelForward'], 'TTC': r['Range1TimeToCollisionForward'], 'class': "vehicle"}

        ctx['cipv'] = obs

    if id == 1969:
        if 'cipv' in ctx:
            ctx['cipv']['pos_lat'] = r['Range1PosLateral']
            ctx['cipv']['vel_lat'] = r['Range1VelLateral']

            ret = ctx['cipv'].copy()
            ctx.pop('cipv')
            return ret
