#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file    :   j2.py    
@contact :   caofulin@minieye.cc
@date    :   2020/12/31 下午2:06
"""


import cantools
db_j2 = cantools.database.load_file('dbc/j2/hb_Obstacle.dbc', strict=False)


def parser_j2(id, buf, ctx=None):

    ids = [m.frame_id for m in db_j2.messages]
    if id not in ids:
        return None

    r = db_j2.decode_message(id, buf, decode_choices=False)

    if id == 1040:
        if 'obs' in ctx:
            obs_list = []
            for i in range(10):
                if i in ctx['obs']:
                    obs = ctx['obs'][i]
                    if not obs.get('valid'):
                        continue
                    obs['type'] = 'obstacle'
                    obs['sensor'] = 'j2'
                    obs_list.append(obs.copy())
                    obs.clear()

            ctx.clear()
            return obs_list

        ctx["obs"] = {}
        ctx['obs']['cipv_id'] = r['ID_CIPV']
        ctx['obs']['cipv_ttc'] = r['CIPV_TTC']

    # obs data [0-5] * 10
    if 1056 <= id <= 1105:

        # no header
        if 'obs' not in ctx:
            return None

        idx = (id - 1056) // 5

        if idx not in ctx['obs']:
            ctx['obs'][idx] = {}

        if "ObstacleID" in r:
            ctx['obs'][idx]["id"] = r['ObstacleID']
            ctx['obs'][idx]['valid'] = r['ObstacleValid']
            ctx['obs'][idx]['class'] = r['ObstacleClass']

        if "ObstacleLength" in r:
            ctx['obs'][idx]['length'] = r['ObstacleLength']
            ctx['obs'][idx]['width'] = r['ObstacleWidth']
            ctx['obs'][idx]['height'] = r['ObstacleHeight']
            ctx['obs'][idx]['cipo'] = r['CIPVFlag']

        if "ObstaclePosX" in r:
            ctx['obs'][idx]['pos_lon'] = r['ObstaclePosX']
            ctx['obs'][idx]['pos_lat'] = -r['ObstaclePosY']
            ctx['obs'][idx]['vel_lon'] = r['ObstacleVelX']
            ctx['obs'][idx]['vel_lat'] = r['ObstacleVelY']
            ctx['obs'][idx]['acc_lon'] = r['ObstacleAccX']

        if 'ObstaclePosXSTD' in r:
            pass

        if 'ObstacleAngle' in r:
            ctx['obs'][idx]['angle'] = r['ObstacleAngle']
