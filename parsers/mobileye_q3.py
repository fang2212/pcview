import time
import cantools

db_ifv300 = cantools.database.load_file('dbc/if300_inst_all.dbc', strict=False)
# db_q3_pv = cantools.database.load_file('/home/nan/workshop/doc/eyeQ3/dbc/PB_Vehicle_CAN_V1.9.0_1.dbc', strict=False)
# db_q3_pv.add_dbc_file('/home/nan/workshop/doc/eyeQ3/dbc/PCAN_v06_11_(s)_Lite_1.dbc')
db_q3 = cantools.database.load_file('dbc/q3/meObs3_v6.dbc', strict=False)
db_q3.add_dbc_file('dbc/q3/meLanes3_v4.dbc')


obs = {}
obs_list = []
lanes = {}
cipv = 0


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
    # if 'VIS_LANE_RIGHT_PARALL_A0' in r:
    #     # print("0x%x" % id, r)
    #     return {'type': 'lane', 'class': 'right_parall', 'a0': r['VIS_LANE_RIGHT_PARALL_A0'],
    #             'a1': r['VIS_LANE_RIGHT_PARALL_A1'],
    #             'a2': r['VIS_LANE_RIGHT_PARALL_A2'], 'a3': r['VIS_LANE_RIGHT_PARALL_A3'],
    #             'range': r['VIS_LANE_RIGHT_PARALL_RANGE'], 'color': 2}
    # if 'VIS_LANE_LEFT_PARALL_A0' in r:
    #     # print("0x%x" % id, r)
    #     return {'type': 'lane', 'class': 'left_parall', 'a0': r['VIS_LANE_LEFT_PARALL_A0'],
    #             'a1': r['VIS_LANE_LEFT_PARALL_A1'],
    #             'a2': r['VIS_LANE_LEFT_PARALL_A2'], 'a3': r['VIS_LANE_LEFT_PARALL_A3'],
    #             'range': r['VIS_LANE_LEFT_PARALL_RANGE'], 'color': 5}
    if 'VIS_LANE_RIGHT_INDIVID_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_RIGHT_INDIVID_RANGE'] > 0:
            return {'type': 'lane', 'id': 0, 'class': 'right_indiv', 'a0': r['VIS_LANE_RIGHT_INDIVID_A0'],
                    'a1': r['VIS_LANE_RIGHT_INDIVID_A1'],
                    'a2': r['VIS_LANE_RIGHT_INDIVID_A2'], 'a3': r['VIS_LANE_RIGHT_INDIVID_A3'],
                    'range': r['VIS_LANE_RIGHT_INDIVID_RANGE'], 'color': 5}
    if 'VIS_LANE_LEFT_INDIVID_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_LEFT_INDIVID_RANGE'] > 0:
            return {'type': 'lane', 'id': 1, 'class': 'left_indiv', 'a0': r['VIS_LANE_LEFT_INDIVID_A0'],
                    'a1': r['VIS_LANE_LEFT_INDIVID_A1'],
                    'a2': r['VIS_LANE_LEFT_INDIVID_A2'], 'a3': r['VIS_LANE_LEFT_INDIVID_A3'],
                    'range': r['VIS_LANE_LEFT_INDIVID_RANGE'], 'color': 5}

    if 'VIS_LANE_NEIGHBOR_RIGHT_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_NEIGHBOR_RIGHT_RANGE'] > 0:
            return {'type': 'lane', 'id': 2, 'class': 'left_indiv', 'a0': r['VIS_LANE_NEIGHBOR_RIGHT_A0'],
                    'a1': r['VIS_LANE_NEIGHBOR_RIGHT_A1'],
                    'a2': r['VIS_LANE_NEIGHBOR_RIGHT_A2'], 'a3': r['VIS_LANE_NEIGHBOR_RIGHT_A3'],
                    'range': r['VIS_LANE_NEIGHBOR_RIGHT_RANGE'], 'color': 5}

    if 'VIS_LANE_NEIGHBOR_LEFT_A0' in r:
        # print("0x%x" % id, r)
        if r['VIS_LANE_NEIGHBOR_LEFT_RANGE'] > 0:
            return {'type': 'lane', 'id': 3, 'class': 'left_indiv', 'a0': r['VIS_LANE_NEIGHBOR_LEFT_A0'],
                    'a1': r['VIS_LANE_NEIGHBOR_LEFT_A1'],
                    'a2': r['VIS_LANE_NEIGHBOR_LEFT_A2'], 'a3': r['VIS_LANE_NEIGHBOR_LEFT_A3'],
                    'range': r['VIS_LANE_NEIGHBOR_LEFT_RANGE'], 'color': 5}

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
            obs['color'] = 5 # blue
            # send = obs.copy()
            # print(send)
            obs_list.append(obs.copy())
            obs.clear()

        if r['VIS_OBS_COUNT_MSG3'] == 15:
            # print('q3 epoch end')
            return obs_list
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
               'sensor_source': r[pf + 'DetectionSensor']}
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
        ctx['rt'][idx]['color'] = 5

        ret = ctx['rt'][idx]
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
               'sensor': r[pf + 'DetectionSensor'], 'color': 6}
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
        if ret['status'] in ['updated', 'coasted', 'new coasted', 'new updated', 'new', 'merged']:
            # print('rts', ret)
            return ret

    if 0x105 == id:
        # print(r)
        pass

obs1 = {}
lanes1 = {}
numofobs = 0


def parse_q3(id, buf, ctx=None):
    ids = [m.frame_id for m in db_q3.messages]
    # global numofobs
    if id not in ids:
        return None
    r = db_q3.decode_message(id, buf)
    if ctx.get('parser_mode') == 'direct':
        return r
    # print("0x%x" % id, r)
    if not ctx.get('obs'):
        ctx['obs'] = {}
    if not ctx.get('obsnum'):
        ctx['obsnum'] = {}

    if id == 0x760:
        speed = buf[2]
        print("vehicle speed:", speed)

    if id == 0x738:
        numofobs = r['NumObstacles']
        timestamp = r['Timestamp']

    if 0x739 + 3 * ctx['obsnum'] > id >= 0x739 and (id - 0x739) % 3 == 0:
        # print()
        # print("0x%x" % id, r)
        ctx['obs']['type'] = 'obstacle'
        ctx['obs']['sensor'] = 'q3'
        ctx['obs']['id'] = r.get('ObstacleID')
        ctx['obs']['pos_lon'] = r['ObstaclePosX']
        ctx['obs']['pos_lat'] = r['ObstaclePosY']
        ctx['obs']['turn_indic'] = r['BlinkerInfo']
        ctx['obs']['cut_in_out'] = r['Move_in_and_Out']
        ctx['obs']['vel_lon'] = r['ObstacleVelX']
        ctx['obs']['class'] = r['ObstacleType']
        ctx['obs']['status'] = r['ObstacleStatus']
        ctx['obs']['brake_indic'] = r['ObstacleBrakeLights']
        ctx['obs']['valid'] = r['ObstacleValid']

    if 0x739 + 3 * ctx['obsnum'] > id >= 0x739 and (id - 0x73a) % 3 == 0:
        ctx['obs']['width'] = r['ObstacleWidth']
        ctx['obs']['cipv'] = r['CIPVFlag']

    if 0x739 + 3 * ctx['obsnum'] > id >= 0x739 and (id - 0x73b) % 3 == 0:
        ctx['obs']['vel_lat'] = r['ObstacleVelY']
        ctx['obs']['acc_lon'] = r['Object_Accel_X']
        ctx['obs']['color'] = 5
        send = ctx['obs'].copy()
        # print(send)
        ctx['obs'].clear()
        # print(send)
        return send

