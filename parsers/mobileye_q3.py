import time
import cantools

from player.ui import CVColor

db_ifv300 = cantools.database.load_file('dbc/if300_inst_all.dbc', strict=False)
# db_q3_pv = cantools.database.load_file('/home/nan/workshop/doc/eyeQ3/dbc/PB_Vehicle_CAN_V1.9.0_1.dbc', strict=False)
# db_q3_pv.add_dbc_file('/home/nan/workshop/doc/eyeQ3/dbc/PCAN_v06_11_(s)_Lite_1.dbc')
db_q3 = cantools.database.load_file('dbc/q3/meObs3_v6.dbc', strict=False)
db_q3.add_dbc_file('dbc/q3/meLanes3_v4.dbc')


obs = {}
obs_list = []
lanes = {}
cipv = 0
vision_color = (255, 144, 30)
fusion_color = CVColor.Blue


def parse_ifv300(id, buf, ctx=None):
    # print(db_q3.messages)
    if id == 0x3e9 or id == 0x330 or id == 0x340:  # discard
        return None
    if id == 32 or id == 715 or id == 986 or id == 781 or id == 804:
        return None
    # print('hello')
    try:
        r = db_ifv300.decode_message(id, buf)
    except Exception as e:
        # print('error', e)
        return
    # print("0x%x" % id, r)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    if 0x401 <= id <= 0x493:  # pedestrian
        if 'TrackID' in r:
            return {'type': 'pedestrian', 'id': r['TrackID'], 'x': r['L_lat_rel'], 'y': r['L_long_rel']}
    if 'CAN_VEHICLE_SPEED' in r:    # 0x440
        # print("0x%x" % id, r)
        # print(r['CAN_VEHICLE_SPEED']*3.6)
        # print("vehicle speed: {} yaw_rate: {}".format(r['CAN_VEHICLE_SPEED'], r['CAN_VEHICLE_YAW_RATE']))
        return {'type': 'vehicle_state', 'speed': r['CAN_VEHICLE_SPEED']*3.6, 'yaw_rate': r['CAN_VEHICLE_YAW_RATE']}
    if 'VIS_LANE_RIGHT_INDIVID_A0' in r:    # 0x6ab
        # print("0x%x" % id, r)
        if r['VIS_LANE_RIGHT_INDIVID_RANGE'] > 0:
            return {'type': 'lane', 'id': 0, 'class': 'right_indiv', 'a0': r['VIS_LANE_RIGHT_INDIVID_A0'],
                    'a1': r['VIS_LANE_RIGHT_INDIVID_A1'],
                    'a2': r['VIS_LANE_RIGHT_INDIVID_A2'], 'a3': r['VIS_LANE_RIGHT_INDIVID_A3'],
                    'range': r['VIS_LANE_RIGHT_INDIVID_RANGE']}
    if 'VIS_LANE_LEFT_INDIVID_A0' in r:     # 0x6ac
        # print("0x%x" % id, r)
        if r['VIS_LANE_LEFT_INDIVID_RANGE'] > 0:
            return {'type': 'lane', 'id': 1, 'class': 'left_indiv', 'a0': r['VIS_LANE_LEFT_INDIVID_A0'],
                    'a1': r['VIS_LANE_LEFT_INDIVID_A1'],
                    'a2': r['VIS_LANE_LEFT_INDIVID_A2'], 'a3': r['VIS_LANE_LEFT_INDIVID_A3'],
                    'range': r['VIS_LANE_LEFT_INDIVID_RANGE']}

    if 'VIS_LANE_NEIGHBOR_RIGHT_A0' in r:       # 0x6a8
        # print("0x%x" % id, r)
        if r['VIS_LANE_NEIGHBOR_RIGHT_RANGE'] > 0:
            return {'type': 'lane', 'id': 2, 'class': 'left_indiv', 'a0': r['VIS_LANE_NEIGHBOR_RIGHT_A0'],
                    'a1': r['VIS_LANE_NEIGHBOR_RIGHT_A1'],
                    'a2': r['VIS_LANE_NEIGHBOR_RIGHT_A2'], 'a3': r['VIS_LANE_NEIGHBOR_RIGHT_A3'],
                    'range': r['VIS_LANE_NEIGHBOR_RIGHT_RANGE']}

    if 'VIS_LANE_NEIGHBOR_LEFT_A0' in r:      # 0x6a9
        # print("0x%x" % id, r)
        if r['VIS_LANE_NEIGHBOR_LEFT_RANGE'] > 0:
            return {'type': 'lane', 'id': 3, 'class': 'left_indiv', 'a0': r['VIS_LANE_NEIGHBOR_LEFT_A0'],
                    'a1': r['VIS_LANE_NEIGHBOR_LEFT_A1'],
                    'a2': r['VIS_LANE_NEIGHBOR_LEFT_A2'], 'a3': r['VIS_LANE_NEIGHBOR_LEFT_A3'],
                    'range': r['VIS_LANE_NEIGHBOR_LEFT_RANGE']}

    if 'VIS_OBS_CIPV' in r:  # 0x671
        global cipv
        cipv = r['VIS_OBS_CIPV']
        # return {'type': 'CIPV', 'id': r['VIS_OBS_CIPV']}

    if 'VIS_OBS_COUNT_MSG1' in r:  # 0x675
        # print("0x%x" % id, r)
        idx = '%02d' % r['VIS_OBS_COUNT_MSG1']
        if r['VIS_OBS_COUNT_MSG1'] == 1:
            # print('q3 epoch start')
            obs_list.clear()
        if r['VIS_OBS_ID_' + idx] == 0:
            return
        obs['id'] = r['VIS_OBS_ID_' + idx]
        if obs['id'] == cipv:
            obs['cipo'] = True
        else:
            obs['cipo'] = False
        obs['type'] = 'obstacle'
        obs['sensor'] = 'ifv300'
        obs['class'] = r['VIS_OBS_CLASSIFICATION_'+idx]
        obs['height'] = r['VIS_OBS_HEIGHT_'+idx]
        obs['ped_waist_up'] = r['VIS_OBS_PED_WAIST_UP_'+idx]
        obs['brake_indic'] = r['VIS_OBS_BRAKE_LIGHT_INDIC_'+idx]
        obs['turn_indic'] = r['VIS_OBS_TURN_INDICATOR_'+idx]
        # return {'type': 'obstacle', 'id': r['VIS_OBS_ID_'+idx], 'height': r['VIS_OBS_HEIGHT_'+idx]}
    if 'VIS_OBS_COUNT_MSG2' in r:       # 0x676
        # print("0x%x" % id, r)
        # print(r)
        idx = '%02d' % r['VIS_OBS_COUNT_MSG2']
        if obs.get('id') is None:
            return
        obs['a_lon'] = r['VIS_OBS_LONG_ACCEL_'+idx]
        obs['CIPO'] = r['VIS_OBS_CIPO_'+idx]
        # print(obs['CIPO'])
        # if obs['id'] == cipv:
        obs['TTC'] = r['VIS_OBS_TTC_CONST_ACC_MODEL_'+idx]
        obs['cut_in_out'] = r['VIS_OBS_CUT_IN_OUT_'+idx]
        # return {'type': 'obstacle', 'a_lon': r['VIS_OBS_LONG_ACCEL_'+idx], 'CIPO': r['VIS_OBS_CIPO_'+idx]}
    if 'VIS_OBS_COUNT_MSG3' in r:       # 0x677
        # print("0x%x" % id, r)
        # x = cos(angle * pi / 180.0) * range
        # y = sin(angle * pi / 180.0) * range
        # print(r)
        idx = '%02d' % r['VIS_OBS_COUNT_MSG3']
        if obs.get('CIPO') is not None:
            # print(idx)
            yaw = 0
            rg = (r['VIS_OBS_LONG_POS_' + idx] ** 2 + r['VIS_OBS_LAT_POS_' + idx] ** 2) ** 0.5
            obs['width'] = r['VIS_OBS_WIDTH_' + idx]
            obs['pos_lon'] = r['VIS_OBS_LONG_POS_' + idx]  # + cos(yaw * pi / 180.0) * rg
            obs['vel_lon'] = r['VIS_OBS_LONG_VEL_' + idx]  # + sin(yaw * pi / 180.0) * rg
            obs['pos_lat'] = r['VIS_OBS_LAT_POS_' + idx]
            obs['vel_lat'] = r['VIS_OBS_LAT_VEL_' + idx]
            obs['color'] = vision_color       # blue
            obs["status_show"] = [{"text": "vision color", "height": 180, "style": vision_color, "size": 0.6}]
            # send = obs.copy()
            # print(send)
            obs_list.append(obs.copy())
            obs.clear()

        if r['VIS_OBS_COUNT_MSG3'] == 15:
            # print('q3 epoch end')
            return obs_list

    # q3  fusion
    if id in [0x760, 0x765, 0x76a, 0x76f, 0x774, 0x779]:  # RT(1-6)A_DIS
        # print('RTxA msg')
        if ctx.get('rt') is None:
            ctx['rt'] = []
        idx = int((id - 0x760) / 5)
        if idx == 0:
            ctx['rt'].clear()
        pf = 'RT{}A_'.format(idx + 1)
        res = {'type': 'obstacle', 'sensor': 'ifv300', 'idx': idx, 'pos_lon': r[pf + 'L_long_rel'], 'pos_lat': r[pf + 'L_lat_rel'],
               'a_lon': r[pf + 'A_long_obj'], 'vel_lon': r[pf + 'V_long_obj'], 'vel_lat': r[pf + 'V_lat_obj'],
               'sensor_source': r[pf + 'DetectionSensor'], "color": CVColor.Blue, "cipo": True if id == 0x760 else False,
               "status_show": [{"text": "fusion color", "height": 160, "style": fusion_color, "size": 0.6}]}
        ctx['rt'].append(res)
        return

    if id in [0x761, 0x766, 0x76b, 0x770, 0x775, 0x77a]:
        # print('RTxB msg')
        if ctx.get('rt') is None:
            return
        idx = int((id - 0x761) / 5)
        pf = 'RT{}B_'.format(idx + 1)
        if len(ctx['rt']) < idx + 1:
            return
        ctx['rt'][idx]['id'] = r[pf + 'TrackID']
        ctx['rt'][idx]['status'] = r[pf + 'Status']
        ctx['rt'][idx]['move'] = r[pf + 'Movement']
        ctx['rt'][idx]['a_lat'] = r[pf + 'A_lat_obj']
        ctx['rt'][idx]['cipo'] = True if id == 0x761 else False,

        return

    if id in [0x762, 0x767, 0x76c, 0x771, 0x776, 0x77b]:
        # print('RTxC msg')
        if ctx.get('rt') is None:
            return
        idx = int((id - 0x762) / 5)
        if len(ctx['rt']) < idx + 1 or ctx['rt'][idx].get('status') is None:
            return
        pf = 'RT{}C_'.format(idx + 1)
        idx = int((id - 0x762) / 5)
        if len(ctx['rt']) < idx + 1:
            return
        ctx['rt'][idx]['vis_id'] = r[pf + 'visTrkID']
        ctx['rt'][idx]['width'] = r[pf + 'Width']
        ctx['rt'][idx]['class'] = r[pf + 'MC_object_class']
        ctx['rt'][idx]['cipo'] = True if id == 0x762 else False,

        ret = ctx['rt'][idx]
        ret["color"] = fusion_color
        ret["status_show"] = [{"text": "fusion color", "height": 160, "style": fusion_color, "size": 0.6}]
        if ret['status'] in ['updated', 'coasted', 'new coasted', 'new updated', 'new', 'merged']:
            # print('rt', ret)
            return ret

    if id in [0x740, 0x745, 0x74a, 0x74f]:
        # print('RTSxA msg')
        if ctx.get('rts') is None:
            ctx['rts'] = []
        idx = int((id - 0x740) / 5)
        pf = 'RTS{}A_'.format(idx + 1)
        if idx == 0:
            ctx['rts'].clear()
        res = {'type': 'obstacle', 'idx': idx, 'id': r[pf + 'TrackID'], 'pos_lon': r[pf + 'L_long_rel'],
               'pos_lat': r[pf + 'L_lat_rel'], 'a_lon': r[pf + 'A_long_obj'], 'status': r[pf + 'Status'],
               'sensor': r[pf + 'DetectionSensor'], 'color': fusion_color,
               "status_show": [{"text": "fusion color", "height": 160, "style": fusion_color, "size": 0.6}]}
        ctx['rts'].append(res)
        return

    if id in [0x741, 0x746, 0x74b, 0x750]:
        # print('RTSxB msg')
        if ctx.get('rts') is None:
            return
        idx = int((id - 0x741) / 5)
        pf = 'RTS{}B_'.format(idx + 1)
        if len(ctx['rts']) < idx + 1:
            return
        ctx['rts'][idx]['vel_lon'] = r[pf + 'V_long_obj']
        ctx['rts'][idx]['vel_lat'] = r[pf + 'V_lat_obj']
        ctx['rts'][idx]['a_lat'] = r[pf + 'A_lat_obj']
        ctx['rts'][idx]['move'] = r[pf + 'Movement']
        return

    if id in [0x742, 0x747, 0x74c, 0x751]:
        # print('RTSxC msg')
        if ctx.get('rts') is None:
            return
        idx = int((id - 0x742) / 5)
        pf = 'RTS{}C_'.format(idx + 1)
        if len(ctx['rts']) < idx + 1:
            return
        ctx['rts'][idx]['width'] = r[pf + 'Width']
        ctx['rts'][idx]['vis_id'] = r[pf + 'visTrkID']
        ctx['rts'][idx]['class'] = r[pf + 'MC_object_class']

        ret = ctx['rts'][idx]
        ret["color"] = fusion_color
        ret["status_show"] = [{"text": "fusion color", "height": 160, "style": fusion_color, "size": 0.6}]
        if ret['status'] in ['updated', 'coasted', 'new coasted', 'new updated', 'new', 'merged']:
            # print('rts', ret)
            return ret

    if 0x105 == id:
        # print(r)
        pass

def parse_ifv300_vision(id, buf, ctx=None):
    # print(db_q3.messages)
    if id == 0x3e9 or id == 0x330 or id == 0x340:  # discard
        return None
    if id == 32 or id == 715 or id == 986 or id == 781 or id == 804:
        return None
    # print('hello')
    try:
        r = db_ifv300.decode_message(id, buf)
    except Exception as e:
        # print('error', e)
        return
    # print("0x%x" % id, r)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    if 'VIS_LANE_RIGHT_INDIVID_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_RIGHT_INDIVID_RANGE'] > 0:
            return {'type': 'lane', 'id': 0, 'class': 'right_indiv', 'a0': r['VIS_LANE_RIGHT_INDIVID_A0'],
                    'a1': r['VIS_LANE_RIGHT_INDIVID_A1'],
                    'a2': r['VIS_LANE_RIGHT_INDIVID_A2'], 'a3': r['VIS_LANE_RIGHT_INDIVID_A3'],
                    'range': r['VIS_LANE_RIGHT_INDIVID_RANGE']}
    if 'VIS_LANE_LEFT_INDIVID_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_LEFT_INDIVID_RANGE'] > 0:
            return {'type': 'lane', 'id': 1, 'class': 'left_indiv', 'a0': r['VIS_LANE_LEFT_INDIVID_A0'],
                    'a1': r['VIS_LANE_LEFT_INDIVID_A1'],
                    'a2': r['VIS_LANE_LEFT_INDIVID_A2'], 'a3': r['VIS_LANE_LEFT_INDIVID_A3'],
                    'range': r['VIS_LANE_LEFT_INDIVID_RANGE']}

    if 'VIS_LANE_NEIGHBOR_RIGHT_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_NEIGHBOR_RIGHT_RANGE'] > 0:
            return {'type': 'lane', 'id': 2, 'class': 'left_indiv', 'a0': r['VIS_LANE_NEIGHBOR_RIGHT_A0'],
                    'a1': r['VIS_LANE_NEIGHBOR_RIGHT_A1'],
                    'a2': r['VIS_LANE_NEIGHBOR_RIGHT_A2'], 'a3': r['VIS_LANE_NEIGHBOR_RIGHT_A3'],
                    'range': r['VIS_LANE_NEIGHBOR_RIGHT_RANGE']}

    if 'VIS_LANE_NEIGHBOR_LEFT_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_NEIGHBOR_LEFT_RANGE'] > 0:
            return {'type': 'lane', 'id': 3, 'class': 'left_indiv', 'a0': r['VIS_LANE_NEIGHBOR_LEFT_A0'],
                    'a1': r['VIS_LANE_NEIGHBOR_LEFT_A1'],
                    'a2': r['VIS_LANE_NEIGHBOR_LEFT_A2'], 'a3': r['VIS_LANE_NEIGHBOR_LEFT_A3'],
                    'range': r['VIS_LANE_NEIGHBOR_LEFT_RANGE']}

    if 'VIS_OBS_CIPV' in r:  # 0x671
        global cipv
        cipv = r['VIS_OBS_CIPV']
        # return {'type': 'CIPV', 'id': r['VIS_OBS_CIPV']}

    if 'VIS_OBS_COUNT_MSG1' in r:  # 0x675
        # print("0x%x" % id, r)
        idx = '%02d' % r['VIS_OBS_COUNT_MSG1']
        if r['VIS_OBS_COUNT_MSG1'] == 1:
            # print('q3 epoch start')
            obs_list.clear()
        if r['VIS_OBS_ID_' + idx] == 0:
            return
        obs['id'] = r['VIS_OBS_ID_' + idx]
        if obs['id'] == cipv:
            obs['cipo'] = True
        else:
            obs['cipo'] = False
        obs['type'] = 'obstacle'
        obs['sensor'] = 'ifv300'
        obs['class'] = r['VIS_OBS_CLASSIFICATION_'+idx]
        obs['height'] = r['VIS_OBS_HEIGHT_'+idx]
        obs['ped_waist_up'] = r['VIS_OBS_PED_WAIST_UP_'+idx]
        obs['brake_indic'] = r['VIS_OBS_BRAKE_LIGHT_INDIC_'+idx]
        obs['turn_indic'] = r['VIS_OBS_TURN_INDICATOR_'+idx]
        # return {'type': 'obstacle', 'id': r['VIS_OBS_ID_'+idx], 'height': r['VIS_OBS_HEIGHT_'+idx]}
    if 'VIS_OBS_COUNT_MSG2' in r:
        # print(r)
        idx = '%02d' % r['VIS_OBS_COUNT_MSG2']
        if obs.get('id') is None:
            return
        obs['a_lon'] = r['VIS_OBS_LONG_ACCEL_'+idx]
        obs['CIPO'] = r['VIS_OBS_CIPO_'+idx]
        # print(obs['CIPO'])
        # if obs['id'] == cipv:
        obs['TTC'] = r['VIS_OBS_TTC_CONST_ACC_MODEL_'+idx]
        obs['cut_in_out'] = r['VIS_OBS_CUT_IN_OUT_'+idx]
        # return {'type': 'obstacle', 'a_lon': r['VIS_OBS_LONG_ACCEL_'+idx], 'CIPO': r['VIS_OBS_CIPO_'+idx]}
    if 'VIS_OBS_COUNT_MSG3' in r:

        # x = cos(angle * pi / 180.0) * range
        # y = sin(angle * pi / 180.0) * range
        # print(r)
        idx = '%02d' % r['VIS_OBS_COUNT_MSG3']
        if obs.get('CIPO') is not None:
            # print(idx)
            yaw = 0
            rg = (r['VIS_OBS_LONG_POS_' + idx] ** 2 + r['VIS_OBS_LAT_POS_' + idx] ** 2) ** 0.5
            obs['width'] = r['VIS_OBS_WIDTH_' + idx]
            obs['pos_lon'] = r['VIS_OBS_LONG_POS_' + idx]  # + cos(yaw * pi / 180.0) * rg
            obs['vel_lon'] = r['VIS_OBS_LONG_VEL_' + idx]  # + sin(yaw * pi / 180.0) * rg
            obs['pos_lat'] = r['VIS_OBS_LAT_POS_' + idx]
            obs['vel_lat'] = r['VIS_OBS_LAT_VEL_' + idx]

            obs_list.append(obs.copy())
            obs.clear()

        if r['VIS_OBS_COUNT_MSG3'] == 15:
            # print('q3 epoch end')
            return obs_list
    if 'CAN_VEHICLE_SPEED' in r:
        # print(r['CAN_VEHICLE_SPEED']*3.6)
        # print("vehicle speed: {} yaw_rate: {}".format(r['CAN_VEHICLE_SPEED'], r['CAN_VEHICLE_YAW_RATE']))
        return {'type': 'vehicle_state', 'speed': r['CAN_VEHICLE_SPEED']*3.6, 'yaw_rate': r['CAN_VEHICLE_YAW_RATE']}

def parse_ifv300_fusion(id, buf, ctx=None):
    # print(db_q3.messages)
    if id == 0x3e9 or id == 0x330 or id == 0x340:  # discard
        return None
    if id == 32 or id == 715 or id == 986 or id == 781 or id == 804:
        return None
    # print('hello')
    try:
        r = db_ifv300.decode_message(id, buf)
    except Exception as e:
        # print('error', e)
        return
    # print("0x%x" % id, r)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    if 0x401 <= id <= 0x493:  # pedestrian
        if 'TrackID' in r:
            return {'type': 'pedestrian', 'id': r['TrackID'], 'x': r['L_lat_rel'], 'y': r['L_long_rel']}
    if 'VIS_LANE_RIGHT_INDIVID_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_RIGHT_INDIVID_RANGE'] > 0:
            return {'type': 'lane', 'id': 0, 'class': 'right_indiv', 'a0': r['VIS_LANE_RIGHT_INDIVID_A0'],
                    'a1': r['VIS_LANE_RIGHT_INDIVID_A1'],
                    'a2': r['VIS_LANE_RIGHT_INDIVID_A2'], 'a3': r['VIS_LANE_RIGHT_INDIVID_A3'],
                    'range': r['VIS_LANE_RIGHT_INDIVID_RANGE']}
    if 'VIS_LANE_LEFT_INDIVID_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_LEFT_INDIVID_RANGE'] > 0:
            return {'type': 'lane', 'id': 1, 'class': 'left_indiv', 'a0': r['VIS_LANE_LEFT_INDIVID_A0'],
                    'a1': r['VIS_LANE_LEFT_INDIVID_A1'],
                    'a2': r['VIS_LANE_LEFT_INDIVID_A2'], 'a3': r['VIS_LANE_LEFT_INDIVID_A3'],
                    'range': r['VIS_LANE_LEFT_INDIVID_RANGE']}

    if 'VIS_LANE_NEIGHBOR_RIGHT_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_NEIGHBOR_RIGHT_RANGE'] > 0:
            return {'type': 'lane', 'id': 2, 'class': 'left_indiv', 'a0': r['VIS_LANE_NEIGHBOR_RIGHT_A0'],
                    'a1': r['VIS_LANE_NEIGHBOR_RIGHT_A1'],
                    'a2': r['VIS_LANE_NEIGHBOR_RIGHT_A2'], 'a3': r['VIS_LANE_NEIGHBOR_RIGHT_A3'],
                    'range': r['VIS_LANE_NEIGHBOR_RIGHT_RANGE']}

    if 'VIS_LANE_NEIGHBOR_LEFT_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_NEIGHBOR_LEFT_RANGE'] > 0:
            return {'type': 'lane', 'id': 3, 'class': 'left_indiv', 'a0': r['VIS_LANE_NEIGHBOR_LEFT_A0'],
                    'a1': r['VIS_LANE_NEIGHBOR_LEFT_A1'],
                    'a2': r['VIS_LANE_NEIGHBOR_LEFT_A2'], 'a3': r['VIS_LANE_NEIGHBOR_LEFT_A3'],
                    'range': r['VIS_LANE_NEIGHBOR_LEFT_RANGE']}

    if 'VIS_OBS_CIPV' in r:  # 0x671
        global cipv
        cipv = r['VIS_OBS_CIPV']
        # return {'type': 'CIPV', 'id': r['VIS_OBS_CIPV']}

    if 'CAN_VEHICLE_SPEED' in r:
        # print(r['CAN_VEHICLE_SPEED']*3.6)
        # print("vehicle speed: {} yaw_rate: {}".format(r['CAN_VEHICLE_SPEED'], r['CAN_VEHICLE_YAW_RATE']))
        return {'type': 'vehicle_state', 'speed': r['CAN_VEHICLE_SPEED']*3.6, 'yaw_rate': r['CAN_VEHICLE_YAW_RATE']}

    # q3  fusion
    if id in [0x760, 0x765, 0x76a, 0x76f, 0x774, 0x779]:  # RT(1-6)A_DIS
        # print('RTxA msg')
        if ctx.get('rt') is None:
            ctx['rt'] = []
        idx = int((id - 0x760) / 5)
        if idx == 0:
            ctx['rt'].clear()
        pf = 'RT{}A_'.format(idx + 1)
        res = {'type': 'obstacle', 'sensor': 'ifv300', 'idx': idx, 'pos_lon': r[pf + 'L_long_rel'], 'pos_lat': r[pf + 'L_lat_rel'],
               'a_lon': r[pf + 'A_long_obj'], 'vel_lon': r[pf + 'V_long_obj'], 'vel_lat': r[pf + 'V_lat_obj'],
               'sensor_source': r[pf + 'DetectionSensor'], "color": CVColor.Blue}
        ctx['rt'].append(res)
        return

    if id in [0x761, 0x766, 0x76b, 0x770, 0x775, 0x77a]:
        # print('RTxB msg')
        if ctx.get('rt') is None:
            return
        idx = int((id - 0x761) / 5)
        pf = 'RT{}B_'.format(idx + 1)
        if len(ctx['rt']) < idx + 1:
            return
        ctx['rt'][idx]['id'] = r[pf + 'TrackID']
        ctx['rt'][idx]['status'] = r[pf + 'Status']
        ctx['rt'][idx]['move'] = r[pf + 'Movement']
        ctx['rt'][idx]['a_lat'] = r[pf + 'A_lat_obj']

        return

    if id in [0x762, 0x767, 0x76c, 0x771, 0x776, 0x77b]:
        # print('RTxC msg')
        if ctx.get('rt') is None:
            return
        idx = int((id - 0x762) / 5)
        if len(ctx['rt']) < idx + 1 or ctx['rt'][idx].get('status') is None:
            return
        pf = 'RT{}C_'.format(idx + 1)
        idx = int((id - 0x762) / 5)
        if len(ctx['rt']) < idx + 1:
            return
        ctx['rt'][idx]['vis_id'] = r[pf + 'visTrkID']
        ctx['rt'][idx]['width'] = r[pf + 'Width']
        ctx['rt'][idx]['class'] = r[pf + 'MC_object_class']

        ret = ctx['rt'][idx]
        ret["color"] = CVColor.Blue
        if ret['status'] in ['updated', 'coasted', 'new coasted', 'new updated', 'new', 'merged']:
            # print('rt', ret)
            return ret

    if id in [0x740, 0x745, 0x74a, 0x74f]:
        # print('RTSxA msg')
        if ctx.get('rts') is None:
            ctx['rts'] = []
        idx = int((id - 0x740) / 5)
        pf = 'RTS{}A_'.format(idx + 1)
        if idx == 0:
            ctx['rts'].clear()
        res = {'type': 'obstacle', 'idx': idx, 'id': r[pf + 'TrackID'], 'pos_lon': r[pf + 'L_long_rel'],
               'pos_lat': r[pf + 'L_lat_rel'], 'a_lon': r[pf + 'A_long_obj'], 'status': r[pf + 'Status'],
               'sensor': r[pf + 'DetectionSensor'], 'color': CVColor.Blue}
        ctx['rts'].append(res)
        return

    if id in [0x741, 0x746, 0x74b, 0x750]:
        # print('RTSxB msg')
        if ctx.get('rts') is None:
            return
        idx = int((id - 0x741) / 5)
        pf = 'RTS{}B_'.format(idx + 1)
        if len(ctx['rts']) < idx + 1:
            return
        ctx['rts'][idx]['vel_lon'] = r[pf + 'V_long_obj']
        ctx['rts'][idx]['vel_lat'] = r[pf + 'V_lat_obj']
        ctx['rts'][idx]['a_lat'] = r[pf + 'A_lat_obj']
        ctx['rts'][idx]['move'] = r[pf + 'Movement']
        return

    if id in [0x742, 0x747, 0x74c, 0x751]:
        # print('RTSxC msg')
        if ctx.get('rts') is None:
            return
        idx = int((id - 0x742) / 5)
        pf = 'RTS{}C_'.format(idx + 1)
        if len(ctx['rts']) < idx + 1:
            return
        ctx['rts'][idx]['width'] = r[pf + 'Width']
        ctx['rts'][idx]['vis_id'] = r[pf + 'visTrkID']
        ctx['rts'][idx]['class'] = r[pf + 'MC_object_class']

        ret = ctx['rts'][idx]
        ret["color"] = CVColor.Blue
        if ret['status'] in ['updated', 'coasted', 'new coasted', 'new updated', 'new', 'merged']:
            # print('rts', ret)
            return ret

obs1 = {}
lanes1 = {}
numofobs = 0
id_table = {0x766: 0, 0x767: 0, 0x768: 1, 0x769: 1, 0x76c: 2, 0x76d: 2, 0x76e: 3, 0x76f: 3}


def parse_q3(id, buf, ctx=None):
    ids = [m.frame_id for m in db_q3.messages]
    global numofobs
    if id not in ids:
        return None
    r = db_q3.decode_message(id, buf)
    if ctx.get('parser_mode') == 'direct':
        return r
    # print("0x%x" % id, r)
    if not ctx.get('obsq3'):
        ctx['obsq3'] = {}
    if not ctx.get('laneq3'):
        ctx['laneq3'] = {}
        ctx['num_of_q3_lane'] = 0
    if not ctx.get('obsnum'):
        ctx['obsnum'] = {}

    if id == 0x760:
        speed = buf[2]
        print("vehicle speed:", speed)

    elif id == 0x738:
        numofobs = r['NumObstacles']
        timestamp = r['Timestamp']

    elif 0x739 + 3 * numofobs > id >= 0x739 and (id - 0x739) % 3 == 0:
        # print()
        # print("0x%x" % id, r)
        ctx['obsq3']['type'] = 'obstacle'
        ctx['obsq3']['sensor'] = 'mbq3'
        ctx['obsq3']['id'] = r.get('ObstacleID')
        ctx['obsq3']['pos_lon'] = r['ObstaclePosX']
        ctx['obsq3']['pos_lat'] = r['ObstaclePosY']
        ctx['obsq3']['turn_indic'] = r['BlinkerInfo']
        ctx['obsq3']['cut_in_out'] = r['Move_in_and_Out']
        ctx['obsq3']['vel_lon'] = r['ObstacleVelX']
        ctx['obsq3']['class'] = r['ObstacleType']
        ctx['obsq3']['status'] = r['ObstacleStatus']
        ctx['obsq3']['brake_indic'] = r['ObstacleBrakeLights']
        ctx['obsq3']['valid'] = r['ObstacleValid']

    elif 0x739 + 3 * numofobs > id >= 0x739 and (id - 0x73a) % 3 == 0:
        ctx['obsq3']['width'] = r['ObstacleWidth']
        ctx['obsq3']['cipo'] = False if r['CIPVFlag'] == 'not CIPV' else True

    elif 0x739 + 3 * numofobs > id >= 0x739 and (id - 0x73b) % 3 == 0:
        ctx['obsq3']['vel_lat'] = r['ObstacleVelY']
        ctx['obsq3']['acc_lon'] = r['Object_Accel_X']
        send = None
        if "pos_lon" in ctx['obsq3'] and ctx['obsq3']['pos_lon'] > 0:

            send = ctx['obsq3'].copy()

        # print(send)
        ctx['obsq3'].clear()
        # print(send)
        return send

    elif id == 0x76b:  # road information
        res = {'type': 'road_info', 'sensor': 'mbq3'}
        res['construction_area'] = r['Construction_Area']
        res['road_type'] = r['Road_Type']
        res['highway_exit_left'] = r['Highway_Exit_Left']
        res['highway_exit_right'] = r['Highway_Exit_Right']
        res['prob_left_lane'] = r['Probability_Of_Left_Lane']
        res['prob_right_lane'] = r['Probability_Of_Right_Lane']
        res['driving_speed_left_lane'] = r['Driving_Speed_Left_Lane']
        res['driving_speed_right_lane'] = r['Driving_Speed_Right_Lane']
        return res

    elif 0x766 <= id <= 0x76f:
        lane_id = id_table.get(id)
        if lane_id not in ctx['laneq3']:
            ctx['laneq3'][lane_id] = {}

        if 'Position' in r:
            res = {'type': 'lane', 'sensor': 'mbq3', 'id': lane_id}
            res['quality'] = r['Quality']
            res['a0'] = r['Position']
            res['a2'] = r['Curvature']
            res['a3'] = r['Curvature_Derivative']
            res['width_marking'] = r['Lane_mark_width']
            ctx['laneq3'][lane_id].update(res)

        elif 'Heading_Angle' in r:
            ctx['laneq3'][lane_id]['a1'] = r['Heading_Angle']
            ctx['laneq3'][lane_id]['range'] = r['View_Range_End']
            ctx['laneq3'][lane_id]['range_start'] = r['View_Range_Start']

    if id == 0x76d:  # last frame of lane
    # if ctx['num_of_q3_lane'] >= 8:
        ctx['num_of_q3_lane'] = 0
        send = list(ctx['laneq3'].copy().values())
        ctx['laneq3'].clear()

        send = [x for x in send if 'a0' in x and 'a1' in x]
        # for item in send:
        # print(send)
        return send


