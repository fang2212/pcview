#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file    :   j2.py    
@contact :   caofulin@minieye.cc
@date    :   2020/12/31 下午2:06
"""


import cantools
db_j2 = cantools.database.load_file('dbc/j2/hb_Obstacle.dbc', strict=False)
db_j2.add_dbc_file('dbc/j2/hb_Lanes.dbc')


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
                    if not obs.get('valid') or not obs['class']:
                        continue
                    obs['type'] = 'obstacle'

                    if obs['class'] == 2:
                        obs['class'] = 'pedestrian'
                    obs['sensor'] = 'j2'
                    obs_list.append(obs.copy())
                    obs.clear()

            ctx['obs'].clear()
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

    if 1281 <= id <= 1288:

        if 1285 <= id <= 1288:
            ld = (id - 1285) % 2 + 2
            lane_key = 'lane_' + str(ld)
            if lane_key not in ctx:
                ctx[lane_key] = {}
        elif 1281 <= id <= 1284:
            ld = (id - 1281) // 2
            lane_key = 'lane_' + str(ld)
            if lane_key not in ctx:
                ctx[lane_key] = {}

        if 'LaneModelC0' in r:
            ctx[lane_key]['a0'] = -r['LaneModelC0']
            ctx[lane_key]['a1'] = r['LaneModelC1']
            ctx[lane_key]['a2'] = r['LaneModelC2']
            ctx[lane_key]['a3'] = r['LaneModelC3']

        if 'LaneTrackID' in r:
            ctx[lane_key]['Lane_Type'] = r['LaneTypeClass']
            ctx[lane_key]['Quality'] = r['LaneQuality']
            ctx[lane_key]['WidthMarking'] = r['LaneWidthMarking']
            ctx[lane_key]['ViewRangeStart'] = r['LaneViewRangeStart']
            ctx[lane_key]['range'] = r['LaneViewRangeEnd']
            ctx[lane_key]['LineMarkColor'] = r['LaneMarkColor']
            ctx[lane_key]['LaneMeasuringStatus'] = r['LaneMeasuringStatus']
            ctx[lane_key]['id'] = ld
            ctx[lane_key]['type'] = 'lane'
            ctx[lane_key]['sensor'] = 'j2'

        if "a0" in ctx[lane_key] and 'type' in ctx[lane_key]:
            # invalid
            obs = None
            if ctx[lane_key]['Lane_Type'] != 15 and ctx[lane_key]['LaneMeasuringStatus'] != 4:
                obs = ctx[lane_key].copy()
            ctx.pop(lane_key)
            return obs


