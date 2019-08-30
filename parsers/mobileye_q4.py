#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   mobileye_q4.py
@Contact :   caofulin@minieye.cc
@Description:   
@Create Time:     2019/8/29 上午10:38   
"""
import cantools

db_q4 = cantools.database.load_file('dbc/q4/Car_sensor_V1.3.dbc', strict=False)
db_q4.add_dbc_file('dbc/q4/Lanes_V1.8.dbc')
db_q4.add_dbc_file('dbc/q4/Objects_V1.4.dbc')


def parser_mbq4(id, buf, ctx):
    ids = [m.frame_id for m in db_q4.messages]
    if id not in ids:
        return None

    r = db_q4.decode_message(id, buf)

    if not r:
        return None

    ## 341
    if id == 0x155:
        return {'type': 'vehicle_state', 'speed': r['CIN_Vehicle_Speed']*3.6, 'yaw_rate': r['CIN_Vehicle_Yaw']}


    ## 0x140  header
    if id == 0x140:
        ctx['lane_header'] = 1

    lane_class = ['left_lane', 'right_lane', 'next_right_lane', 'next_left_lane']
    if 0x141 <= id <= 0x14F:

        lane_type = lane_class[(id-0x141) // 4]

        if 'lane_header' not in ctx:
            return None

        if lane_type not in ctx:
            ctx[lane_type] = {}
        if 'Lane_View_Range_End' in r:
            ctx[lane_type]['range'] = r['Lane_View_Range_End']
        if 'is_Lane_Valid' in r:
            ctx[lane_type]['vaild'] = True if r['is_Lane_Valid'] == "TRUE" else False
            # print('vaild', ctx[lane_type]['vaild'])
        for i in range(0, 4):
            key = 'Lane_C' + str(i)
            if key in r:
                ctx[lane_type]['a' + str(i)] = -r[key]
        if (id-0x141 + 1)%4 == 0:
            if len(ctx[lane_type]) >= 5:
                ctx[lane_type]['color'] = 8 # grey
                ctx[lane_type]['type'] = 'lane'
                ctx[lane_type]['class'] = lane_type
                res = ctx[lane_type].copy()
                ctx[lane_type].clear()
                # if 'vaild' in res and res['vaild']:
                #     return res
                return res
            ctx[lane_type].clear()

    if id == 0x110:
        ctx['obs_header'] = 1
        ctx['cipv_id'] = r['OBJ_VD_CIPV_ID']

    # 0x110 header
    if 0x111 <= id <= 0x138:

        if 'obs_header' not in ctx:
            return None

        obs_idx = (id - 0x111) // 4
        now_key = "obs_" + str(obs_idx)
        if now_key not in ctx:
            ctx[now_key] = {}

        if 'OBJ_ID' in r:
            ctx[now_key]['id'] = r['OBJ_ID']
            ctx[now_key]['class'] = r['OBJ_Object_Class']

            if ctx[now_key]['id'] == ctx['cipv_id']:
                ctx[now_key]['cipo'] = True
            else:
                ctx[now_key]['cipo'] = False
            # print('class', ctx[now_key]['class'])
        if 'OBJ_Lat_Distance' in r:
            ctx[now_key]['pos_lat'] = -r['OBJ_Lat_Distance']
        if 'OBJ_Long_Distance' in r:
            ctx[now_key]['pos_lon'] = r['OBJ_Long_Distance']

        if 'OBJ_Length' in r:
            ctx[now_key]['height'] = r['OBJ_Length'] / 3
            ctx[now_key]['width'] = r['OBJ_Width']

        if (id-0x111 + 1)%4 == 0:
            if len(ctx[now_key]) >= 6:
                ctx[now_key]['color'] = 8
                ctx[now_key]['type'] = 'obstacle'
                ctx[now_key]['sensor'] = 'mbq4'
                res = ctx[now_key].copy()
                # print(res)
                ctx[now_key].clear()
                return res
            ctx[now_key].clear()

