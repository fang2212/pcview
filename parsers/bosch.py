#!/usr/bin/env python
# _*_ coding:utf-8 _*_
from math import sqrt, pi, atan2

import cantools

# 前视雷达
bosch_db = cantools.database.load_file('dbc/FR5CP_SFCAN_Matrix_V1_20201202_Released.dbc', strict=False)
# 前后左右角雷达
bosch_rr_db = cantools.database.load_file('dbc/CR5CP_RR_SFCAN_Matrix_V1_20201202_Released.dbc', strict=False)
bosch_rl_db = cantools.database.load_file('dbc/CR5CP_RL_SFCAN_Matrix_V1_20201202_Released.dbc', strict=False)
bosch_fr_db = cantools.database.load_file('dbc/CR5CP_FR_SFCAN_Matrix_V1_20201202_Released.dbc', strict=False)
bosch_fl_db = cantools.database.load_file('dbc/CR5CP_FL_SFCAN_Matrix_V1_20201202_Released.dbc', strict=False)

# can id列表
ids = [m.frame_id for m in bosch_db.messages]
ids_rl = [m.frame_id for m in bosch_rl_db.messages]

cipv = {}
cipp = {}
x1_lane = {}
detection_sensor = {
    0: 'no_matched_measurements',
    1: 'single_radar_only',
    2: 'multi_radar_only',
    3: 'vision_only',
    4: 'radar and vision',
}

mrr_status = {}


def bosch_mrr(cid, data, ctx=None):
    """
    博世前视雷达
    :param cid:
    :param data:
    :param ctx:
    :return:
    """
    if cid not in ids:
        return None
    r = bosch_db.decode_message(cid, data)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    # print("0x%x" % id, r)
    if not ctx.get('bosch_obs'):
        ctx['bosch_obs'] = list()
    if cid == 0x200:
        mrr_status["status"] = r["FR5CP_FailureStatus"]

    if 0x203 <= cid <= 0x20a:
        # other car
        index = cid - 0x203
        # 因中间少了个0x207，所以后面的需要做一下特殊处理
        index = index - 1 if index > 4 else index

        start_num = index * 5 + 1
        end_num = 33 if index == 6 else start_num + 5
        for i in range(start_num, end_num):
            if r["FR5CP_ObjExistProb_{}".format(i)] > 0:
                data = {
                    "source": ctx["source"],
                    'type': 'obstacle',
                    'sensor': 'bosch',
                    'sensor_type': 'radar',
                    'id': r["FR5CP_ObjID_{}".format(i)],
                    'pos_lon': r["FR5CP_ObjDistX_{}".format(i)],
                    'pos_lat': -r["FR5CP_ObjDistY_{}".format(i)],
                    'vel_lon': r["FR5CP_ObjRelVelX_{}".format(i)],
                    'vel_lat': -r["FR5CP_ObjRelVelY_{}".format(i)],
                }
                # data['range'] = sqrt(data['pos_lon']**2 + data['pos_lat']**2)
                data['angle'] = atan2(data['pos_lat'], data['pos_lon']) * 180 / pi
                ttc = data['pos_lon'] / -data['vel_lon'] if data['vel_lon'] < 0 else 7
                if ttc > 7:
                    ttc = 7
                # 状态框显示信息
                data["status_show"] = [
                    {"text": "status:{}".format(mrr_status.get("status", "Failure"))}
                    # {"text": "TTC:{:.2f}s".format(ttc)},
                    # {"text": 'R/A: {:.2f} / {:.2f}'.format(data["pos_lon"], data['angle'])}
                ]
                ctx['bosch_obs'].append(data)

        if cid == 0x20a:
            r = ctx['bosch_obs'].copy()
            ctx['bosch_obs'].clear()
            return r


def bosch_rl(cid, data, ctx=None):
    """
    前左角雷达
    :param cid:
    :param data:
    :param ctx:
    :return:
    """
    if cid in ids_rl:
        if not ctx.get('bosch_rl_obs'):
            ctx['bosch_rl_obs'] = list()

        r = bosch_rl_db.decode_message(cid, data)
        if cid == 0x277:
            mrr_status["status"] = r["FR5CP_FailureStatus"]
            if r["CR5CP_FLFailureSt"] != 'No failure':
                print('CR5CP_FLFailureSt: '+r["CR5CP_FLFailureSt"])
            if r['CR5CP_FRFailureSt'] != 'No failure':
                print('CR5CP_FRFailureSt: '+ r["CR5CP_FRFailureSt"])
            if r['CR5CP_RRFailureSt'] != 'No failure':
                print('CR5CP_RRFailureSt: ' + r["CR5CP_RRFailureSt"])
            if r['CR5CP_RLFailureSt'] != 'No failure':
                print('CR5CP_RLFailureSt: ' + r["CR5CP_RLFailureSt"])
        if cid == 0x27A:
            print('CR5CP_RL_Obj_timestamp: {}'.format(r['CR5CP_RL_Obj_timestamp']))
            if r['CR5CP_RL_Sensor_Dirty']:
                print('CR5CP_RL_Sensor_Dirty: {}'.format(r['CR5CP_RL_Sensor_Dirty']))
            if r['CR5CP_RL_SGU_Failure'] !='No failure':
                print('CR5CP_RL_SGU_Failure : '+ r['CR5CP_RL_SGU_Failure'])
        if cid == 0x268:
            if r['CR5CP_RL_BLIND'] == 'Active':
                print('CR5CP_RL_BLIND: '+ r['CR5CP_RL_BLIND'])
            # if r['CR5CP_RL_Alig_Never_DONE'] == 'Active':
            #     print('CR5CP_RL_Alig_Never_DONE: '+ r['CR5CP_RL_Alig_Never_DONE'])
            # if r['CR5CP_RL_Alig_NOT_OK'] == 'Active':
            #     print('CR5CP_RL_Alig_NOT_OK: '+ r['CR5CP_RL_Alig_NOT_OK'])
            if r['CR5CP_RL_MisAlig'] == 'Active':
                print('CR5CP_RL_MisAlig: '+ r['CR5CP_RL_MisAlig'])
        if 0x337 <= cid <= 0x339 or cid == 0x343:
            index = cid - 0x337
            index = 3 if index > 3 else index
            start_num = index * 4 + 1
            end_num = start_num + 4
            # print('CR5CP_RLObj{}Locat:'.format(index+1)+' {}'.format(r['CR5CP_RLObj{}Locat_x'.format(index+1)])
            #       +' {}'.format(r['CR5CP_RLObj{}Locat_y'.format(index+1)]) +' {}'.format(r['CR5CP_RLObj{}Locat_theta'.format(index+1)]))
            for i in range(start_num, end_num):
                if r["CR5CP_RL_ObjExistProb_{}".format(i)] > 0:
                    # print('CR5CP_RL_ObjExistProbr: {}'.format(r["CR5CP_RL_ObjExistProb_{}".format(i)]))
                    data = {
                        'type': 'obstacle',
                        'sensor': 'bosch',
                        'id': r["CR5CP_RL_ObjID_{}".format(i)],
                        'pos_lon': r["CR5CP_RL_ObjDistX_{}".format(i)],
                        'pos_lat': -r["CR5CP_RL_ObjDistY_{}".format(i)],
                        'vel_lon': r["CR5CP_RL_ObjRelVelX_{}".format(i)],
                        'vel_lat': -r["CR5CP_RL_ObjRelVelY_{}".format(i)],
                        'accel_x':r["CR5CP_RL_ObjAccelX_{}".format(i)],
                        'dyn_prop':0,
                        'color': 1
                    }
                    prob_exit = r["CR5CP_RL_ObjExistProb_{}".format(i)]
                    prob_obs= r["CR5CP_RL_ObjObstacleProb_{}".format(i)]
                    rr = sqrt(data['pos_lon']**2 + data['pos_lat']**2)
                    angle = atan2(data['pos_lat'], data['pos_lon']) * 180 / pi
                    ret = {'type': 'obstacle', 'id': data['id'], 'pos_lon': data['pos_lon'], 'pos_lat': data['pos_lat'], 'range': rr,
                           'angle': angle,
                           'range_rate': data['vel_lon'], 'v_lon': data['vel_lon'], 'v_lat': data['vel_lat'], 'power': data['accel_x'], 'dyn_prop':'dyn_prop_%03d' % data['dyn_prop'],
                           'tgt_status': 'State_%07f' %(int(prob_exit*100)+prob_obs), 'color': 1}
                    bosch_cr5cp_rl_obs.append(ret)

if __name__ == "__main__":
    bosch_mrr(0x20a, bytes().fromhex("00000002004010068032000000000002004010068032000000000000000794e4"), {})
    # parse_bosch(0x209, bytes().fromhex("00000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000076d89"), {})
    # parse_bosch(0x206, bytes().fromhex("00000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000076d89"), {})