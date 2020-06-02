#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   mobileye_q4.py
@Contact :   caofulin@minieye.cc
@Description:   
@Create Time:     2019/8/29 上午10:38   
"""
import cantools
import time

db_q4 = cantools.database.load_file('dbc/q4/Car_sensor_V1.3.dbc', strict=False)
db_q4.add_dbc_file('dbc/q4/Lanes_V1.8_fix.dbc')
db_q4.add_dbc_file('dbc/q4/Objects_V1.4.dbc')
db_q4.add_dbc_file('dbc/q4/TSR_V1.3.dbc')

obs = {}
ids = [m.frame_id for m in db_q4.messages]


def parser_mbq4(id, buf, ctx):
    if id not in ids:
        return None
    # t0 = time.time()
    r = db_q4.decode_message(id, buf)
    # dt = time.time() - t0
    # print('q4 decode cost: {:.2f}ms'.format(dt*1000))
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    if not r:
        return None
    # print(r)

    ## 341
    if id == 0x155:
        return {'type': 'vehicle_state', 'speed': r['CIN_Vehicle_Speed']*3.6, 'yaw_rate': r['CIN_Vehicle_Yaw']}

    ## 0x140  header
    if id == 0x140:
        ctx['lane_header'] = 1

    lane_class = ['left_lane', 'right_lane', 'next_right_lane', 'next_left_lane']
    if 0x141 <= id <= 0x150:
        lane_type = lane_class[(id-0x141) // 4]
        if 'lane_header' not in ctx:
            return None

        if lane_type not in ctx:
            ctx[lane_type] = {}

        # lane Data A
        if 'Lane_Track_ID' in r:
            ctx[lane_type]['track_ID'] = r['Lane_Track_ID']
            ctx[lane_type]['probability'] = r['Lane_Exist_Probability']
            ctx[lane_type]['type_class'] = r['Lane_Type_Class']
            ctx[lane_type]['range_start'] = r['Lane_View_Range_Start']
            ctx[lane_type]['range'] = r['Lane_View_Range_End']
            ctx[lane_type]['lane_color_det'] = r['Lane_Color']
            ctx[lane_type]['lane_DLM_type'] = r['Lane_DLM_Type']

            # only in left and right lane
            if 'is_Lane_Valid' in r:
                ctx[lane_type]['vaild'] = r['is_Lane_Valid'] == "TRUE"
                ctx[lane_type]['lane_crossing'] = r['Lane_Crossing']

        # lane Data B
        if 'Line_Marker_Width' in r:
            ctx[lane_type]['marker_width'] = r['Line_Marker_Width']
            ctx[lane_type]['dash_average_length'] = r['Dash_Average_Length']
            ctx[lane_type]['dash_average_gap'] = r['Dash_Average_Gap']
            # only in left and right lane
            if 'Prediction_Source' in r:
                ctx[lane_type]['prediction_source'] = r['Prediction_Source']
            else:
                ctx[lane_type]['prediction_source'] = 'NONE'

        # C0-C3
        for i in range(0, 4):
            key = 'Lane_C' + str(i)
            if key in r:
                ctx[lane_type]['a' + str(i)] = -r[key]

        if (id-0x141 + 1)%4 == 0:
            tt = len(ctx[lane_type])
            if len(ctx[lane_type]) >= 5 and ctx[lane_type]['track_ID'] > 0:
                ctx[lane_type]['id'] = lane_type
                ctx[lane_type]['color'] = 8
                ctx[lane_type]['type'] = 'lane'
                ctx[lane_type]['class'] = lane_type

                res = ctx[lane_type].copy()
                ctx[lane_type].clear()
                return res
            # ctx[lane_type].clear()

    if id == 0x110:
        ctx['obs_header'] = 1
        ctx['cipv_id'] = r['OBJ_VD_CIPV_ID']

    # 0x110 header  Obj
    if 0x111 <= id <= 0x138:
        if 'obs_header' not in ctx:
            return None

        obs_idx = (id - 0x111) // 4
        cur_id_key = "obs_" + str(obs_idx)
        if cur_id_key not in ctx:
            ctx[cur_id_key] = {}

        # Data A
        if 'OBJ_ID' in r:
            ctx[cur_id_key]['id'] = r['OBJ_ID']
            ctx[cur_id_key]['probability'] = r['OBJ_Existence_Probability']
            ctx[cur_id_key]['status'] = r['OBJ_Measuring_Status']
            ctx[cur_id_key]['motion_category'] = r['OBJ_Motion_Category']
            ctx[cur_id_key]['class'] = r['OBJ_Object_Class']
            ctx[cur_id_key]['motion_status'] = r['OBJ_Motion_Status']
            ctx[cur_id_key]['brake_light'] = r['OBJ_Brake_Light']
            ctx[cur_id_key]['turn_right'] = r['OBJ_Turn_Indicator_Right']
            ctx[cur_id_key]['turn_ledt'] = r['OBJ_Turn_Indicator_Left']

            if ctx[cur_id_key]['id'] == ctx['cipv_id']:
                ctx[cur_id_key]['cipo'] = True
            else:
                ctx[cur_id_key]['cipo'] = False
            # print('ID: ', r['OBJ_ID'], 'class', ctx[cur_id_key]['class'])

        # Data B
        if 'OBJ_Lane_Assignment' in r:
            if 'id' not in ctx[cur_id_key]:
                return
            ctx[cur_id_key]['lane_assignment'] = r['OBJ_Lane_Assignment']
            ctx[cur_id_key]['width'] = r['OBJ_Width']
            ctx[cur_id_key]['length'] = r['OBJ_Length']
            ctx[cur_id_key]['height'] = r['OBJ_Width']  # for test
            ctx[cur_id_key]['vel_lon_abs'] = r['OBJ_Abs_Long_Velocity']

        # Data C
        if 'OBJ_Abs_Lat_Velocity' in r:
            if 'id' not in ctx[cur_id_key]:
                return
            ctx[cur_id_key]['vel_lat_abs'] = r['OBJ_Abs_Lat_Velocity']
            ctx[cur_id_key]['acc_lon_abs'] = r['OBJ_Abs_Long_Acc']
            ctx[cur_id_key]['pos_lon'] = r['OBJ_Long_Distance']

        # Data D
        if 'OBJ_Lat_Distance' in r:
            if 'id' not in ctx[cur_id_key]:
                return
            ctx[cur_id_key]['pos_lat'] = -r['OBJ_Lat_Distance'] # eyeq4 坐标系不一样
            ctx[cur_id_key]['angle_rate'] = r['OBJ_Angle_Rate']

        if (id-0x111 + 1) % 4 == 0:
            if len(ctx[cur_id_key]) >= 6:
                ctx[cur_id_key]['color'] = 8
                ctx[cur_id_key]['type'] = 'obstacle'
                ctx[cur_id_key]['sensor'] = 'mbq4'
                res = ctx[cur_id_key].copy()
                # print(res)
                ctx[cur_id_key].clear()
                return res
            ctx[cur_id_key].clear()

    if 0x156 <= id <= 0x16F:
        if 'TSR_ID' in r:
            obs['id'] = r['TSR_ID']
            obs['type'] = 'traffic_sign'
            obs['sign_name'] = r['TSR_Sign_Name']
            obs['confidence'] = r['TSR_Confidence']
            obs['relevancy'] = r['TSR_Relevancy']
            obs['filter_type'] = r['TSR_Filter_Type']
            obs['sup1_sign_name'] = r['TSR_Sup1_SignName']
            obs['sup1_confidence'] = r['TSR_Sup1_Confidence']

        if 'TSR_Sign_Height' in r:
            obs['sup2_sign_name'] = r['TSR_Sup2_SignName']
            obs['sup2_confidence'] = r['TSR_Sup2_Confidence']
            obs['pos_lon'] = r['TSR_Sign_Long_Distance']
            obs['pos_lat'] = -r['TSR_Sign_Lateral_Distance']
            obs['pos_hgt'] = r['TSR_Sign_Height']

            obs['color'] = 8
            obs['sensor'] = 'mbq4'
            res = obs.copy()
            if obs['pos_lon'] > 0.0:
                # print(res)
                return res
                # print('x: ',  r['TSR_Sign_Long_Distance'], 'y: ', r['TSR_Sign_Lateral_Distance'], 'Z: ', r['TSR_Sign_Height'])
            obs.clear()
            # return res
