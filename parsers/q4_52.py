#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import math

import cantools
import time

from utils import logger

db_q4 = cantools.db.load_file('dbc/q4_52/Hazards.dbc', strict=False)
db_q4.add_dbc_file('dbc/q4_52/LanesHost.dbc')
db_q4.add_dbc_file('dbc/q4_52/LanesAdjacent.dbc')
db_q4.add_dbc_file('dbc/q4_52/Objects.dbc')
db_q4.add_dbc_file('dbc/q4_52/opTSR.dbc')

db_car = cantools.db.load_file('dbc/q4_52/Hazards.dbc', strict=False)
db_lane = cantools.db.load_file('dbc/q4_52/LanesHost.dbc', strict=False)
db_lane.add_dbc_file('dbc/q4_52/LanesAdjacent.dbc')
db_obj = cantools.db.load_file('dbc/q4_52/Objects.dbc', strict=False)
db_tsr = cantools.db.load_file('dbc/q4_52/opTSR.dbc', strict=False)

obs = dict()
ids = [m.frame_id for m in db_q4.messages]

ids_car = [m.frame_id for m in db_car.messages]
ids_lane = [m.frame_id for m in db_lane.messages]
ids_obj = [m.frame_id for m in db_obj.messages]
ids_tsr = [m.frame_id for m in db_tsr.messages]
lane_host_class = ['left_lane_host', 'right_lane_host']
lane_class = ['left_lane', 'right_lane', 'next_right_lane', 'next_left_lane']


def parser_q4_52(id, buf, ctx):
    if id not in ids:
        return None
    if 'q4_t0' not in ctx:
        ctx['q4_t0'] = time.time()
        ctx['q4_parse_time'] = 0
        ctx['q4_parse_cnt'] = 0
    t0 = time.time()
    r = db_q4.decode_message(id, buf)
    ctx['q4_parse_cnt'] += 1
    dt = time.time() - t0
    ctx['q4_parse_time'] += dt
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    if not r:
        return None

    if id == 0x155:
        return {'type': 'vehicle_state', 'speed': r['CIN_Vehicle_Speed']*3.6, 'yaw_rate': r['CIN_Vehicle_Yaw']}

    if 'q4_lane' not in ctx:
        ctx['q4_lane'] = {}
    if 'q4_obj' not in ctx:
        ctx['q4_obj'] = {}

    # obj header
    if id == 0x541:
        ctx['q4_cipv_id'] = r["VD_CIPV_ID"]
    elif 0x500 <= id <= 0x523:
        obj_idx = (id - 0x500) // 3
        obj_key = "obj_{}".format(obj_idx)
        if obj_key not in ctx['q4_obj']:
            ctx['q4_obj'][obj_key] = {}

        # data A
        if "Obj_ID_{}".format(obj_idx+1) in r:
            ctx['q4_obj'][obj_key]['type'] = 'obstacle'
            ctx['q4_obj'][obj_key]['sensor'] = 'mbq4'
            ctx['q4_obj'][obj_key]['id'] = r["Obj_ID_{}".format(obj_idx+1)]
            ctx['q4_obj'][obj_key]['width'] = r['OBJ_Width_{}'.format(obj_idx+1)]
            ctx['q4_obj'][obj_key]['length'] = r['OBJ_Length_{}'.format(obj_idx+1)]
            ctx['q4_obj'][obj_key]['vel_lat_rel'] = r["Relative_Lat_Velocity_{}".format(obj_idx+1)]
            ctx['q4_obj'][obj_key]['vel_lon_rel'] = r["Relative_Long_Velocity_{}".format(obj_idx + 1)]
            ctx['q4_obj'][obj_key]['class'] = r["Object_Class_{}".format(obj_idx+1)]
        # data B
        elif "Absolute_Long_Acc_{}".format(obj_idx+1) in r:
            ctx['q4_obj'][obj_key]['pos_lat'] = r["Lateral_Distance_{}".format(obj_idx + 1)]
            ctx['q4_obj'][obj_key]['pos_lon'] = r["Long_Distance_{}".format(obj_idx + 1)]
            ctx['q4_obj'][obj_key]['acc_lon_abs'] = r["Absolute_Long_Acc_{}".format(obj_idx + 1)]
        # data C
        elif "Absolute_Speed_{}".format(obj_idx+1) in r:
            ctx['q4_obj'][obj_key]["angle_rate"] = r["OBJ_Angle_Rate_{}".format(obj_idx + 1)]
            ctx['q4_obj'][obj_key]['motion_category'] = r["OBJ_Motion_Category_{}".format(obj_idx + 1)]
            ctx['q4_obj'][obj_key]['motion_status'] = r["OBJ_Motion_Status_{}".format(obj_idx + 1)]
            ctx['q4_obj'][obj_key]['brake_light'] = r["Brake_Light_{}".format(obj_idx + 1)]
            ctx['q4_obj'][obj_key]['turn_right'] = r["Turn_Indicator_Right_{}".format(obj_idx + 1)]
            ctx['q4_obj'][obj_key]['turn_left'] = r["Turn_Indicator_Left_{}".format(obj_idx + 1)]

        if id == 0x523 and ctx['q4_obj']:
            res = []
            for i in ctx['q4_obj']:
                if not ctx['q4_obj'][i]:
                    continue
                try:
                    if ctx['q4_obj'][i].get('id') == ctx.get('q4_cipv_id'):
                        ctx['q4_obj'][i]['cipo'] = True
                    else:
                        ctx['q4_obj'][i]['cipo'] = False
                    if len(ctx['q4_obj'][i]) >= 17:
                        res.append(ctx['q4_obj'][i].copy())
                except Exception as e:
                    logger.error(e, exc_info=True)
                    logger.error('q4_52 parse error', id, ctx['q4_obj'][i])
            ctx['q4_obj'].clear()
            ctx['q4_cipv_id'] = None
            return res

    # 0x770 lane host header
    if id == 0x76e:
        ctx['lane_host_header'] = 1
    elif 0x770 <= id <= 0x773:
        host_index = (id - 0x770) // 2
        lane_type = lane_host_class[host_index]
        if 'lane_host_header' not in ctx:
            return None
        if lane_type not in ctx["q4_lane"]:
            ctx["q4_lane"][lane_type] = {}

        if "LH_Lanemark_Type" in r:
            ctx['q4_lane'][lane_type]['lane_type'] = r['LH_Lanemark_Type']
            ctx['q4_lane'][lane_type]['probability'] = r['LH_Confidence']
            ctx['q4_lane'][lane_type]["range_start"] = r["LH_VR_Start"]
            ctx['q4_lane'][lane_type]['range'] = r['LH_VR_End']
        elif "LH_C0" in r:
            ctx['q4_lane'][lane_type]['a0'] = r['LH_C0']
            ctx['q4_lane'][lane_type]['a1'] = r['LH_C1']
            ctx['q4_lane'][lane_type]['a2'] = r['LH_C2']
            ctx['q4_lane'][lane_type]['a3'] = r['LH_C3']

        if (id - 0x770 + 1) % 2 == 0 and 'lane_type' in ctx['q4_lane'][lane_type] and 'a0' in ctx['q4_lane'][lane_type]:
            if len(ctx['q4_lane'][lane_type]) >= 8:
                ctx['q4_lane'][lane_type]['id'] = lane_type
                ctx['q4_lane'][lane_type]['type'] = 'lane'
                ctx['q4_lane'][lane_type]['class'] = lane_type

                res = ctx['q4_lane'][lane_type].copy()
                ctx['q4_lane'][lane_type].clear()
                return res

    # 0x782 lane adjacent header
    elif id == 0x782:
        ctx['lane_adjacent_header'] = 1
    elif 0x784 <= id <= 0x78b:
        index = (id-0x784) // 2
        lane_type = lane_class[index]
        if 'lane_adjacent_header' not in ctx:
            return None
        if lane_type not in ctx['q4_lane']:
            ctx['q4_lane'][lane_type] = {}

        # lane Data A
        if 'Adjacent_Type_{}'.format(index+1) in r:
            ctx['q4_lane'][lane_type]['lane_type'] = r['Adjacent_Type_{}'.format(index+1)]
            ctx['q4_lane'][lane_type]['probability'] = r['Adjacent_Confidence_{}'.format(index+1)]
            ctx['q4_lane'][lane_type]['range_start'] = r['Adjacent_View_Range_Start_{}'.format(index+1)]
            ctx['q4_lane'][lane_type]['range'] = r['Adjacent_View_Range_End_{}'.format(index+1)]
        # lane Data B
        elif 'Adjacent_Line_C0_{}'.format(index+1) in r:
            ctx['q4_lane'][lane_type]['a0'] = r['Adjacent_Line_C0_{}'.format(index+1)]
            ctx['q4_lane'][lane_type]['a1'] = r['Adjacent_Line_C1_{}'.format(index + 1)]
            ctx['q4_lane'][lane_type]['a2'] = r['Adjacent_Line_C2_{}'.format(index + 1)]
            ctx['q4_lane'][lane_type]['a3'] = r['Adjacent_Line_C3_{}'.format(index + 1)]

            if lane_type == "left_lane":
                value = math.fabs(round(1/(2*r['Adjacent_Line_C2_{}'.format(index + 1)]), 2))
                ctx['q4_lane'][lane_type]["status_show"] = [
                    {
                        "text": "Rl:{}".format(value if value < 5000 else "straights"),
                        "height": 40
                    }
                ]
            elif lane_type == "right_lane":
                value = math.fabs(round(1/(2*r['Adjacent_Line_C2_{}'.format(index + 1)]), 2))
                ctx['q4_lane'][lane_type]["status_show"] = [
                    {
                        "text": "Rr:{}".format(value if value < 5000 else "straights"),
                        "height": 60
                    }
                ]

        if (id-0x784 + 1) % 2 == 0 and 'lane_type' in ctx['q4_lane'][lane_type] and 'a0' in ctx['q4_lane'][lane_type]:
            if len(ctx['q4_lane'][lane_type]) >= 8:
                ctx['q4_lane'][lane_type]['id'] = lane_type
                ctx['q4_lane'][lane_type]['type'] = 'lane'
                ctx['q4_lane'][lane_type]['class'] = lane_type

                res = ctx['q4_lane'][lane_type].copy()
                ctx['q4_lane'][lane_type].clear()
                # print(res)
                return res
            # ctx['q4_lane'][lane_type].clear()

