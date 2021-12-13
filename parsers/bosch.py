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
ids_rr = [m.frame_id for m in bosch_rr_db.messages]
ids_fl = [m.frame_id for m in bosch_fl_db.messages]
ids_fr = [m.frame_id for m in bosch_fr_db.messages]

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
bosch_status = {}


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


def bosch_f(cid, data, ctx=None):
    """
    博世前车角雷达
    """
    res = bosch_fl(cid, data, ctx=ctx)
    if res is None:
        res = bosch_fr(cid, data, ctx=ctx)
    return res


def bosch_r(cid, data, ctx=None):
    """
    博世后车角雷达
    """
    res = bosch_rl(cid, data, ctx=ctx)
    if res is None:
        res = bosch_rr(cid, data, ctx=ctx)
    return res


def bosch_fl(cid, data, ctx=None):
    """
    前左角雷达
    :param cid:
    :param data:
    :param ctx:
    :return:
    """
    if cid in ids_fl:
        if not ctx.get('bosch_fl_obs'):
            ctx['bosch_fl_obs'] = list()

        r = bosch_fl_db.decode_message(cid, data)
        if 0x331 <= cid <= 0x333 or cid == 0x341:
            index = cid - 0x331
            index = 3 if index > 3 else index
            start_num = index * 4 + 1
            end_num = start_num + 4

            for i in range(start_num, end_num):
                if r["CR5CP_FL_ObjExistProb_{}".format(i)] > 0:
                    ret = {
                        'type': 'obstacle',
                        'sensor': 'bosch_fl',
                        'sensor_type': 'radar',
                        'id': r["CR5CP_FL_ObjID_{}".format(i)],
                        'pos_lon': r["CR5CP_FL_ObjDistX_{}".format(i)],
                        'pos_lat': -r["CR5CP_FL_ObjDistY_{}".format(i)],
                        # 'range': sqrt(r["CR5CP_FL_ObjDistX_{}".format(i)]**2 + (-r["CR5CP_FL_ObjDistY_{}".format(i)])**2),
                        # 'angle': atan2((-r["CR5CP_FL_ObjDistY_{}".format(i)]), r["CR5CP_FL_ObjDistX_{}".format(i)]) * 180 / pi,
                        'range_rate': r["CR5CP_FL_ObjRelVelX_{}".format(i)],
                        'v_lon': r["CR5CP_FL_ObjRelVelX_{}".format(i)],
                        'v_lat': -r["CR5CP_FL_ObjRelVelY_{}".format(i)],
                        'power': r["CR5CP_FL_ObjAccelX_{}".format(i)]
                    }
                    ctx['bosch_fl_obs'].append(ret)
        if 0x32C <= cid <= 0x32F:
            index = cid - 0x32C
            start_num = index * 4 + 1
            end_num = start_num + 4
            for i in range(start_num, end_num):
                if r["CR5CP_FL_ObjNewExistProb_{}".format(i)] > 0:
                    data = {
                        'pos_lon': r["CR5CP_FL_ObjNewDistX_{}".format(i)],
                        'pos_lat': -r["CR5CP_FL_ObjNewDistY_{}".format(i)],#需取反
                        'vel_lon': r["CR5CP_FL_ObjNewRelVelX_{}".format(i)],
                        'vel_lat': -r["CR5CP_FL_ObjNewRelVelY_{}".format(i)],#需取反
                    }
                    # rr = sqrt(data['pos_lon']**2 + data['pos_lat']**2)
                    # angle = atan2(data['pos_lat'], data['pos_lon']) * 180 / pi
                    ret = {
                        'type': 'obstacle',
                        'sensor': 'bosch_fl',
                        'sensor_type': 'radar',
                        'id': r["CR5CP_FL_ObjNewID_{}".format(i)],
                        'pos_lon': data['pos_lon'], 'pos_lat': data['pos_lat'],
                        # 'range': rr,
                        # 'angle': angle,
                        'range_rate': data['vel_lon'],
                        'v_lon': data['vel_lon'],
                        'v_lat': data['vel_lat'],
                    }
                    ctx['bosch_fl_obs'].append(ret)
        if cid == 0x32F:
            r = ctx['bosch_fl_obs'].copy()
            ctx['bosch_fl_obs'].clear()
            return r


def bosch_fr(cid, data, ctx=None):
    """
    前右角雷达
    :param cid:
    :param data:
    :param ctx:
    :return:
    """
    if cid in ids_fr:
        if not ctx.get('bosch_fr_obs'):
            ctx['bosch_fr_obs'] = list()

        r = bosch_fr_db.decode_message(cid, data)
        if 0x334 <= cid <= 0x336 or cid == 0x342:
            index = cid - 0x334
            index = 3 if index > 3 else index
            start_num = index * 4 + 1
            end_num = start_num + 4
            for i in range(start_num, end_num):
                if r["CR5CP_FR_ObjExistProb_{}".format(i)] > 0:
                    data = {
                        'pos_lon': r["CR5CP_FR_ObjDistX_{}".format(i)],
                        'pos_lat': -r["CR5CP_FR_ObjDistY_{}".format(i)],#需取反
                        'vel_lon': r["CR5CP_FR_ObjRelVelX_{}".format(i)],
                        'vel_lat': -r["CR5CP_FR_ObjRelVelY_{}".format(i)],#需取反
                    }
                    ret = {
                        'type': 'obstacle',
                        'sensor': 'bosch_fr',
                        'sensor_type': 'radar',
                        'id': r["CR5CP_FR_ObjID_{}".format(i)]+100,
                        'pos_lon': data['pos_lon'],
                        'pos_lat': data['pos_lat'],
                        'range_rate': data['vel_lon'],
                        'v_lon': data['vel_lon'],
                        'v_lat': data['vel_lat'],
                        }
                    ctx['bosch_fr_obs'].append(ret)
        if 0x33D <= cid <= 0x340:
            index = cid - 0x33D
            index = 3 if index > 3 else index
            start_num = index * 4 + 1
            end_num = start_num + 4
            for i in range(start_num, end_num):
                if r["CR5CP_FR_ObjNewExistProb_{}".format(i)] > 0:
                    data = {
                        'id': r["CR5CP_FR_ObjNewID_{}".format(i)] + 100,
                        'pos_lon': r["CR5CP_FR_ObjNewDistX_{}".format(i)],
                        'pos_lat': -r["CR5CP_FR_ObjNewDistY_{}".format(i)],#需取反
                        'vel_lon': r["CR5CP_FR_ObjNewRelVelX_{}".format(i)],
                        'vel_lat': -r["CR5CP_FR_ObjNewRelVelY_{}".format(i)],#需取反
                    }
                    ret = {
                        'type': 'obstacle',
                        'sensor': 'bosch_fr',
                        'sensor_type': 'radar',
                        'id': data['id'],
                        'pos_lon': data['pos_lon'],
                        'pos_lat': data['pos_lat'],
                        'range_rate': data['vel_lon'],
                        'v_lon': data['vel_lon'],
                        'v_lat': data['vel_lat'],
                    }
                    ctx['bosch_fr_obs'].append(ret)
        if cid == 0x340:
            r = ctx['bosch_fr_obs'].copy()
            ctx['bosch_fr_obs'].clear()
            return r


def bosch_rl(cid, data, ctx=None):
    """
    后左角雷达
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
            if r['CR5CP_RLFailureSt'] != 'No failure':
                bosch_status['rl_status'] = r["CR5CP_RLFailureSt"]
        elif 0x337 <= cid <= 0x339 or cid == 0x343:
            index = cid - 0x337
            index = 3 if index > 3 else index
            start_num = index * 4 + 1
            end_num = start_num + 4
            for i in range(start_num, end_num):
                if r["CR5CP_RL_ObjExistProb_{}".format(i)] > 0:
                    data = {
                        'type': 'obstacle',
                        'sensor': 'bosch_rl',
                        'sensor_type': 'radar',
                        'id': r["CR5CP_RL_ObjID_{}".format(i)],
                        'pos_lon': r["CR5CP_RL_ObjDistX_{}".format(i)],
                        'pos_lat': -r["CR5CP_RL_ObjDistY_{}".format(i)],
                        'vel_lon': r["CR5CP_RL_ObjRelVelX_{}".format(i)],
                        'vel_lat': -r["CR5CP_RL_ObjRelVelY_{}".format(i)],
                        'accel_x':r["CR5CP_RL_ObjAccelX_{}".format(i)],
                    }
                    ctx['bosch_rl_obs'].append(data)
        elif 0x345 <= cid <= 0x348:
            index = cid - 0x345
            start_num = index * 4 + 1
            end_num = start_num + 4
            for i in range(start_num, end_num):
                if r["CR5CP_RL_ObjNewExistProb_{}".format(i)] > 0:
                    data = {
                        'type': 'obstacle',
                        'sensor': 'bosch_rl',
                        'sensor_type': 'radar',
                        'id': r["CR5CP_RL_ObjNewID_{}".format(i)],
                        'pos_lon': r["CR5CP_RL_ObjNewDistX_{}".format(i)],
                        'pos_lat': -r["CR5CP_RL_ObjNewDistY_{}".format(i)],#需取反
                        'vel_lon': r["CR5CP_RL_ObjNewRelVelX_{}".format(i)],
                        'vel_lat': -r["CR5CP_RL_ObjNewRelVelY_{}".format(i)],#需取反
                        'accel_x': r["CR5CP_RL_ObjNewAccelX_{}".format(i)],
                    }
                    ctx['bosch_rl_obs'].append(data)
            if cid == 0x348:
                r = ctx['bosch_rl_obs'].copy()
                ctx['bosch_rl_obs'].clear()
                return r


def bosch_rr(cid, data, ctx=None):
    """
    后右角雷达
    :param cid:
    :param data:
    :param ctx:
    :return:
    """
    if cid in ids_rr:
        if not ctx.get('bosch_rr_obs'):
            ctx['bosch_rr_obs'] = list()

        r = bosch_rr_db.decode_message(cid, data)
        if cid == 0x277:
            if r['CR5CP_RRFailureSt'] != 'No failure':
                bosch_status['rr_status'] = r["CR5CP_RRFailureSt"]
            # elif r['CR5CP_RLFailureSt'] != 'No failure':
            #     bosch_status['rl_status'] = r["CR5CP_RLFailureSt"]
        elif 0x33A <= cid <= 0x33C or cid == 0x344:
            index = cid - 0x33A
            index = 3 if index > 3 else index
            start_num = index * 4 + 1
            end_num = start_num + 4
            for i in range(start_num, end_num):
                if r["CR5CP_RR_ObjExistProb_{}".format(i)] > 0:
                    # print('CR5CP_RR_ObjExistProb {}: '.format(r["CR5CP_RR_ObjExistProb_{}".format(i)]))
                    data = {
                        'type': 'obstacle',
                        'sensor': 'bosch_rr',
                        'sensor_type': 'radar',
                        'id': r["CR5CP_RR_ObjID_{}".format(i)]+100,
                        'pos_lon': r["CR5CP_RR_ObjDistX_{}".format(i)],
                        'pos_lat': -r["CR5CP_RR_ObjDistY_{}".format(i)],#需取反
                        'vel_lon': r["CR5CP_RR_ObjRelVelX_{}".format(i)],
                        'vel_lat': -r["CR5CP_RR_ObjRelVelY_{}".format(i)],#需取反
                        'accel_x':r["CR5CP_RR_ObjAccelX_{}".format(i)],
                        'dyn_prop':10
                    }
                    ctx['bosch_rr_obs'].append(data)
        if 0x349 <= cid <= 0x34B or cid == 0x34D:
            index = cid - 0x349
            index = 3 if index > 3 else index
            start_num = index * 4 + 1
            end_num = start_num + 4
            for i in range(start_num, end_num):
                if r["CR5CP_RR_ObjNewExistProb_{}".format(i)] > 0:
                    data = {
                        'type': 'obstacle',
                        'sensor': 'bosch_rr',
                        'sensor_type': 'radar',
                        'id': r["CR5CP_RR_ObjNewID_{}".format(i)] + 100,
                        'pos_lon': r["CR5CP_RR_ObjNewDistX_{}".format(i)],
                        'pos_lat': -r["CR5CP_RR_ObjNewDistY_{}".format(i)],#需取反
                        'vel_lon': r["CR5CP_RR_ObjNewRelVelX_{}".format(i)],
                        'vel_lat': -r["CR5CP_RR_ObjNewRelVelY_{}".format(i)],#需取反
                        'accel_x':r["CR5CP_RR_ObjNewAccelX_{}".format(i)],
                    }
                    ctx['bosch_rr_obs'].append(data)
        if cid == 0x34D:
            r = ctx['bosch_rr_obs'].copy()
            ctx['bosch_rr_obs'].clear()
            return r


if __name__ == "__main__":
    bosch_mrr(0x20a, bytes().fromhex("00000002004010068032000000000002004010068032000000000000000794e4"), {})
    # parse_bosch(0x209, bytes().fromhex("00000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000076d89"), {})
    # parse_bosch(0x206, bytes().fromhex("00000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000076d89"), {})