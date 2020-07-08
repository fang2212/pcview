#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   mobileye_q4.py
@Contact :   caofulin@minieye.cc
@Description:   
@Create Time:     2019/8/29 上午10:38   
"""
import cantools
# import canmatrix
# import decimal
import time
# from canard import can, bus
# from canard.file import jsondb

db_q4 = cantools.db.load_file('dbc/q4/Car_sensor_V1.3.dbc', strict=False)
db_q4.add_dbc_file('dbc/q4/Lanes_V1.8_fix.dbc')
db_q4.add_dbc_file('dbc/q4/Objects_V1.4.dbc')
db_q4.add_dbc_file('dbc/q4/TSR_V1.3.dbc')
# db_q4 = cantools.db.load_file('dbc/q4/EyeQ4_all.dbc', strict=False)
# with open('dbc/q4/EyeQ4_all.dbc', 'w') as wf:
#     wf.write(db_q4.as_dbc_string())
db_car = cantools.db.load_file('dbc/q4/Car_sensor_V1.3.dbc', strict=False)
db_lane = cantools.db.load_file('dbc/q4/Lanes_V1.8_fix.dbc', strict=False)
db_obj = cantools.db.load_file('dbc/q4/Objects_V1.4.dbc', strict=False)
db_tsr = cantools.db.load_file('dbc/q4/TSR_V1.3.dbc', strict=False)

# db_car = canmatrix.formats.loadp_flat('dbc/q4/Car_sensor_V1.3.dbc')
# db_lane = canmatrix.formats.loadp_flat('dbc/q4/Lanes_V1.8_fix.dbc')
# db_obj = canmatrix.formats.loadp_flat('dbc/q4/Objects_V1.4.dbc')
# db_tsr = canmatrix.formats.loadp_flat('dbc/q4/TSR_V1.3.dbc')
# db_q4_all = canmatrix.formats.loadp_flat('dbc/q4/Car_sensor_V1.3.dbc')

# db_q4_all.merge([db_lane, db_obj, db_tsr])

# parser = jsondb.JsonDbParser()
# db = parser.parse('dbc/q4/EyeQ4_all.json')


obs = {}
ids = [m.frame_id for m in db_q4.messages]

ids_car = [m.frame_id for m in db_car.messages]
ids_lane = [m.frame_id for m in db_lane.messages]
ids_obj = [m.frame_id for m in db_obj.messages]
ids_tsr = [m.frame_id for m in db_tsr.messages]


def parser_mbq4(id, buf, ctx):
    if id not in ids:
        return None
    if 'q4_t0' not in ctx:
        ctx['q4_t0'] = time.time()
        ctx['q4_parse_time'] = 0
        ctx['q4_parse_cnt'] = 0
    # return {'type': 'vehicle_state', 'yaw_rate': 0.7, 'speed': 1.0}
    t0 = time.time()
    r = db_q4.decode_message(id, buf)
    # print('0x{:x}'.format(id), r)


    # if id in ids_lane:
    #     r = db_lane.decode_message(id, buf)
    # elif id in ids_obj:
    #     r = db_obj.decode_message(id, buf)
    # elif id in ids_car:
    #     r = db_car.decode_message(id, buf)
    # elif id in ids_tsr:
    #     r = db_tsr.decode_message(id, buf)
    # else:
    #     return

    # frame = can.Frame(id)
    # data = [x for x in buf]
    # # print(data)
    # frame.data = data
    # frame.dlc = 8
    # signals = db.parse_frame(frame)
    # r = {}
    # # print('0x{:x}'.format(id))
    # if signals:
    #     for sig in signals:
    #         r[sig.name] = sig.value
    #         # print(sig)
    #
    # # return



    # arbitration_id = canmatrix.ArbitrationId(id, extended=False)
    # decoded = db_q4_all.decode(arbitration_id, buf)
    # # print('0x{:x}'.format(id))
    # r = {}
    # for signal, value in decoded.items():
    #     if isinstance(value.named_value, decimal.Decimal):
    #         r[signal] = float(value.named_value)
    #     else:
    #         r[signal] = value.named_value
    #         # print('0x{:x}'.format(id), value.named_value)

    # return
    ctx['q4_parse_cnt'] += 1
    dt = time.time() - t0
    ctx['q4_parse_time'] += dt
    # if ctx['q4_parse_cnt'] == 3000:
    #     print('q4 parse 3000 frames cost:', '{:.2f}ms'.format(ctx['q4_parse_time']*1000))
    # if time.time() - ctx['q4_t0'] >= 1.0:
    #     print('q4 parse frames cost in 1000ms:', '{:.2f}ms'.format(ctx['q4_parse_time'] * 1000))
    #     ctx['q4_parse_time'] = 0
    #     ctx['q4_t0'] = time.time()
    # print('q4 decode cost: {:.2f}ms'.format(dt*1000))
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    if not r:
        return None
    # print('0x{:x}'.format(id), r)
    ## 341
    if id == 0x155:
        return {'type': 'vehicle_state', 'speed': r['CIN_Vehicle_Speed']*3.6, 'yaw_rate': r['CIN_Vehicle_Yaw']}

    ## 0x140  header
    if id == 0x140:
        ctx['lane_header'] = 1
        
    if 'q4_lane' not in ctx:
        ctx['q4_lane'] = {}

    lane_class = ['left_lane', 'right_lane', 'next_right_lane', 'next_left_lane']
    if 0x141 <= id <= 0x150:
        lane_type = lane_class[(id-0x141) // 4]
        if 'lane_header' not in ctx:
            return None

        if lane_type not in ctx['q4_lane']:
            ctx['q4_lane'][lane_type] = {}

        # lane Data A
        if 'Lane_Track_ID' in r:
            ctx['q4_lane'][lane_type]['track_ID'] = r['Lane_Track_ID']
            ctx['q4_lane'][lane_type]['probability'] = r['Lane_Exist_Probability']
            ctx['q4_lane'][lane_type]['type_class'] = r['Lane_Type_Class']
            ctx['q4_lane'][lane_type]['range_start'] = r['Lane_View_Range_Start']
            ctx['q4_lane'][lane_type]['range'] = r['Lane_View_Range_End']
            ctx['q4_lane'][lane_type]['lane_color_det'] = r['Lane_Color']
            ctx['q4_lane'][lane_type]['lane_DLM_type'] = r['Lane_DLM_Type']

            # only in left and right lane
            if 'is_Lane_Valid' in r:
                ctx['q4_lane'][lane_type]['vaild'] = r['is_Lane_Valid'] == "TRUE"
                ctx['q4_lane'][lane_type]['lane_crossing'] = r['Lane_Crossing']

        # lane Data B
        if 'Line_Marker_Width' in r:
            ctx['q4_lane'][lane_type]['marker_width'] = r['Line_Marker_Width']
            ctx['q4_lane'][lane_type]['dash_average_length'] = r['Dash_Average_Length']
            ctx['q4_lane'][lane_type]['dash_average_gap'] = r['Dash_Average_Gap']
            # only in left and right lane
            if 'Prediction_Source' in r:
                ctx['q4_lane'][lane_type]['prediction_source'] = r['Prediction_Source']
            else:
                ctx['q4_lane'][lane_type]['prediction_source'] = 'NONE'

        # C0-C3
        if 'Lane_C0' in r:
            ctx['q4_lane'][lane_type]['a0'] = -r['Lane_C0']
            ctx['q4_lane'][lane_type]['a1'] = -r['Lane_C1']

        if 'Lane_C2' in r:
            ctx['q4_lane'][lane_type]['a2'] = -r['Lane_C2']
            ctx['q4_lane'][lane_type]['a3'] = -r['Lane_C3']

        # for i in range(0, 4):
        #     key = 'Lane_C' + str(i)
        #     if key in r:
        #         ctx['q4_lane'][lane_type]['a' + str(i)] = -r[key]

        if (id-0x141 + 1) % 4 == 0 and 'track_ID' in ctx['q4_lane'][lane_type] and 'marker_width' in ctx['q4_lane'][lane_type]:
            tt = len(ctx['q4_lane'][lane_type])
            if 'a0' not in ctx['q4_lane'][lane_type] or 'a2' not in ctx['q4_lane'][lane_type]:
                return
            if len(ctx['q4_lane'][lane_type]) >= 5 and ctx['q4_lane'][lane_type]['track_ID'] > 0:
                ctx['q4_lane'][lane_type]['id'] = lane_type
                ctx['q4_lane'][lane_type]['color'] = 8
                ctx['q4_lane'][lane_type]['type'] = 'lane'
                ctx['q4_lane'][lane_type]['class'] = lane_type

                res = ctx['q4_lane'][lane_type].copy()
                ctx['q4_lane'][lane_type].clear()
                # print(res)
                return res
            # ctx['q4_lane'][lane_type].clear()

    if 'q4_obs' not in ctx:
        ctx['q4_obs'] = {}
        


    # 0x110 header  Obj
    if 0x110 <= id <= 0x138:
        # if 'obs_header' not in ctx:
        #     return None
        if id == 0x110:
            # ctx['obs_header'] = 1
            ctx['q4_cipv_id'] = r['OBJ_VD_CIPV_ID']
        obs_idx = (id - 0x111) // 4
        cur_id_key = "obs_" + str(obs_idx)
        if cur_id_key not in ctx['q4_obs']:
            ctx['q4_obs'][cur_id_key] = {}

        # Data A
        if 'OBJ_ID' in r:
            if r['OBJ_Existence_Probability'] == 0:
                return
            ctx['q4_obs'][cur_id_key]['color'] = 8
            ctx['q4_obs'][cur_id_key]['type'] = 'obstacle'
            ctx['q4_obs'][cur_id_key]['sensor'] = 'mbq4'
            ctx['q4_rcnt'] = r['Rolling_Counter']
            ctx['q4_obs'][cur_id_key]['id'] = r['OBJ_ID']
            ctx['q4_obs'][cur_id_key]['probability'] = r['OBJ_Existence_Probability']
            ctx['q4_obs'][cur_id_key]['status'] = r['OBJ_Measuring_Status']
            ctx['q4_obs'][cur_id_key]['motion_category'] = r['OBJ_Motion_Category']
            ctx['q4_obs'][cur_id_key]['class'] = r['OBJ_Object_Class']
            ctx['q4_obs'][cur_id_key]['motion_status'] = r['OBJ_Motion_Status']
            ctx['q4_obs'][cur_id_key]['brake_light'] = r['OBJ_Brake_Light']
            ctx['q4_obs'][cur_id_key]['turn_right'] = r['OBJ_Turn_Indicator_Right']
            ctx['q4_obs'][cur_id_key]['turn_left'] = r['OBJ_Turn_Indicator_Left']
            # print('ID: ', r['OBJ_ID'], 'class', ctx['q4_obs'][cur_id_key]['class'])

        # Data B
        if 'OBJ_Lane_Assignment' in r:
            if 'id' in ctx['q4_obs'][cur_id_key]:
                ctx['q4_obs'][cur_id_key]['lane_assignment'] = r['OBJ_Lane_Assignment']
                ctx['q4_obs'][cur_id_key]['width'] = r['OBJ_Width']
                ctx['q4_obs'][cur_id_key]['length'] = r['OBJ_Length']
                ctx['q4_obs'][cur_id_key]['height'] = r['OBJ_Width']  # for test
                ctx['q4_obs'][cur_id_key]['vel_lon_abs'] = r['OBJ_Abs_Long_Velocity']

        # Data C
        if 'OBJ_Abs_Lat_Velocity' in r:
            if 'id' in ctx['q4_obs'][cur_id_key]:
                ctx['q4_obs'][cur_id_key]['vel_lat_abs'] = r['OBJ_Abs_Lat_Velocity']
                ctx['q4_obs'][cur_id_key]['acc_lon_abs'] = r['OBJ_Abs_Long_Acc']
                ctx['q4_obs'][cur_id_key]['pos_lon'] = r['OBJ_Long_Distance']

        # Data D
        if 'OBJ_Lat_Distance' in r:
            if 'id' in ctx['q4_obs'][cur_id_key]:
                ctx['q4_obs'][cur_id_key]['pos_lat'] = -r['OBJ_Lat_Distance'] # eyeq4 坐标系不一样
                ctx['q4_obs'][cur_id_key]['angle_rate'] = r['OBJ_Angle_Rate']

        if (id-0x111 + 1) % 4 == 0:
            if 'id' in ctx['q4_obs'][cur_id_key]:
            # if len(ctx['q4_obs'][cur_id_key]) >= 6:
                ctx['q4_obs'][cur_id_key]['color'] = 8
                ctx['q4_obs'][cur_id_key]['type'] = 'obstacle'
                ctx['q4_obs'][cur_id_key]['sensor'] = 'mbq4'
                # res = ctx['q4_obs'][cur_id_key].copy()
                # print(res)
                # ctx['q4_obs'][cur_id_key].clear()
                # return res
            # ctx['q4_obs'][cur_id_key].clear()
        if id == 0x124:  # end of obstacles
            if not ctx.get('q4_rcnt') or not ctx['q4_obs']:
                return
            res = []
            for id in ctx['q4_obs']:
                if not ctx['q4_obs'][id]:
                    continue
                try:
                    if ctx['q4_obs'][id]['id'] == ctx['q4_cipv_id']:
                        ctx['q4_obs'][id]['cipo'] = True
                    else:
                        ctx['q4_obs'][id]['cipo'] = False
                    if len(ctx['q4_obs'][id]) == 23:
                        res.append(ctx['q4_obs'][id])
                except Exception as e:
                    print('q4 parse error', id, ctx['q4_obs'][id])
                    # raise e
            ctx['q4_obs'].clear()
            ctx['q4_cipv_id'] = None

            # print('q4 obs', res)
            return res

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


# db_lane = cantools.db.load_file('dbc/q4/Lanes_V1.8_fix.dbc', strict=False)
# ids_lane = [m.frame_id for m in db_lane.messages]


def parser_mbq4_lane_tsr(id, buf, ctx):
    # if id not in ids_lane:
    #     return None
    if 'q4_t0' not in ctx:
        ctx['q4_t0'] = time.time()
        ctx['q4_parse_time'] = 0
        ctx['q4_parse_cnt'] = 0
    # return {'type': 'vehicle_state', 'yaw_rate': 0.7, 'speed': 1.0}
    t0 = time.time()
    # r = db_lane.decode_message(id, buf)
    if id in ids_lane:
        r = db_lane.decode_message(id, buf)
    elif id in ids_tsr:
        r = db_tsr
    else:
        return
    # return
    ctx['q4_parse_cnt'] += 1
    dt = time.time() - t0
    ctx['q4_parse_time'] += dt
    # if ctx['q4_parse_cnt'] == 3000:
    #     print('q4 parse 3000 frames cost:', '{:.2f}ms'.format(ctx['q4_parse_time']*1000))
    if time.time() - ctx['q4_t0'] >= 1.0:
        print('q4 parse frames cost in 1000ms:', '{:.2f}ms'.format(ctx['q4_parse_time'] * 1000))
        ctx['q4_parse_time'] = 0
        ctx['q4_t0'] = time.time()
    # print('q4 decode cost: {:.2f}ms'.format(dt*1000))
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    if not r:
        return None
    # print('0x{:x}'.format(id), r)
    ## 341
    if id == 0x155:
        return {'type': 'vehicle_state', 'speed': r['CIN_Vehicle_Speed'] * 3.6, 'yaw_rate': r['CIN_Vehicle_Yaw']}

    ## 0x140  header
    if id == 0x140:
        ctx['lane_header'] = 1

    if 'q4_lane' not in ctx:
        ctx['q4_lane'] = {}

    lane_class = ['left_lane', 'right_lane', 'next_right_lane', 'next_left_lane']
    if 0x141 <= id <= 0x150:
        lane_type = lane_class[(id - 0x141) // 4]
        if 'lane_header' not in ctx:
            return None

        if lane_type not in ctx['q4_lane']:
            ctx['q4_lane'][lane_type] = {}

        # lane Data A
        if 'Lane_Track_ID' in r:
            ctx['q4_lane'][lane_type]['track_ID'] = r['Lane_Track_ID']
            ctx['q4_lane'][lane_type]['probability'] = r['Lane_Exist_Probability']
            ctx['q4_lane'][lane_type]['type_class'] = r['Lane_Type_Class']
            ctx['q4_lane'][lane_type]['range_start'] = r['Lane_View_Range_Start']
            ctx['q4_lane'][lane_type]['range'] = r['Lane_View_Range_End']
            ctx['q4_lane'][lane_type]['lane_color_det'] = r['Lane_Color']
            ctx['q4_lane'][lane_type]['lane_DLM_type'] = r['Lane_DLM_Type']

            # only in left and right lane
            if 'is_Lane_Valid' in r:
                ctx['q4_lane'][lane_type]['vaild'] = r['is_Lane_Valid'] == "TRUE"
                ctx['q4_lane'][lane_type]['lane_crossing'] = r['Lane_Crossing']

        # lane Data B
        if 'Line_Marker_Width' in r:
            ctx['q4_lane'][lane_type]['marker_width'] = r['Line_Marker_Width']
            ctx['q4_lane'][lane_type]['dash_average_length'] = r['Dash_Average_Length']
            ctx['q4_lane'][lane_type]['dash_average_gap'] = r['Dash_Average_Gap']
            # only in left and right lane
            if 'Prediction_Source' in r:
                ctx['q4_lane'][lane_type]['prediction_source'] = r['Prediction_Source']
            else:
                ctx['q4_lane'][lane_type]['prediction_source'] = 'NONE'

        # C0-C3
        if 'Lane_C0' in r:
            ctx['q4_lane'][lane_type]['a0'] = -r['Lane_C0']
            ctx['q4_lane'][lane_type]['a1'] = -r['Lane_C1']

        if 'Lane_C2' in r:
            ctx['q4_lane'][lane_type]['a2'] = -r['Lane_C2']
            ctx['q4_lane'][lane_type]['a3'] = -r['Lane_C3']

        # for i in range(0, 4):
        #     key = 'Lane_C' + str(i)
        #     if key in r:
        #         ctx['q4_lane'][lane_type]['a' + str(i)] = -r[key]

        if (id - 0x141 + 1) % 4 == 0 and 'track_ID' in ctx['q4_lane'][lane_type] and 'marker_width' in ctx['q4_lane'][
            lane_type]:
            tt = len(ctx['q4_lane'][lane_type])
            if len(ctx['q4_lane'][lane_type]) >= 5 and ctx['q4_lane'][lane_type]['track_ID'] > 0:
                ctx['q4_lane'][lane_type]['id'] = lane_type
                ctx['q4_lane'][lane_type]['color'] = 8
                ctx['q4_lane'][lane_type]['type'] = 'lane'
                ctx['q4_lane'][lane_type]['class'] = lane_type

                res = ctx['q4_lane'][lane_type].copy()
                ctx['q4_lane'][lane_type].clear()
                # print(res)
                return res
            # ctx['q4_lane'][lane_type].clear()

