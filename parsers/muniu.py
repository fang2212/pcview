#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import time
from math import sqrt, pi, atan2

import cantools

mn_db = cantools.database.load_file('dbc/20210813_T79.dbc', strict=False)

mn_ids = [m.frame_id for m in mn_db.messages]

radar_pos_data = {
    0: dict(),  # FL
    1: dict(),  # FR
    2: dict(),  # RL
    3: dict()   # RR
}


def parser_mu(cid, r):
    """
    解析雷达数据
    :param cid: can id
    :param r: 解析的结果数据
    :return: 渲染数据
    """
    tick = 0
    if 0x421 <= cid <= 0x424:
        index = cid - 0x421

        cur_radar_info = radar_pos_data[index].copy()
        radar_pos_data[index] = dict()
        radar_pos_data[index]['type'] = int(cid - 0x420)  #radar_type[index]
        radar_pos_data[index]['tick'] = tick
        radar_pos_data[index]['data'] = []
        radar_pos_data[index]['sysfloornoise'] = r['Targets_SOF_SysFloorNoise']

        if cur_radar_info:
            return cur_radar_info['data']

    if 0x461 <= cid <= 0x464:
        index = cid - 0x461
        if radar_pos_data[index]:
            radar_pos_data[index]['guardraildis'] = r['TargetsAK_ExtraInfo_GuardrailDis']

    if 0x499 <= cid <= 0x49C:
        index = cid - 0x499
        obj = {'id': int(r['TargetsAK_CartesianCSYS_ID'])+ index * 32,
               'pos_lon': float(r['TargetsAK_CartesianCSYS_X']),
               'pos_lat': -float(r['TargetsAK_CartesianCSYS_Y']),
               'v_lon': float(r['TargetsAK_CartesianCSYS_Vx']),
               'v_lat': -float(r['TargetsAK_CartesianCSYS_Vy']),
               'z': float(r['TargetsAK_CartesianCSYS_Z']),
               'accel_x':0,
               'type': 'obstacle',
               'sensor': 'T79',
               'sensor_type': 'radar'
               }
        # if index > 1:
        #     obj['v_lat'] = -obj['v_lat']
        obj ['range'] = sqrt(obj['pos_lon'] ** 2 + obj['pos_lat'] ** 2)
        obj ['angle'] = atan2(obj['pos_lat'], obj['pos_lon']) * 180 / pi
        obj['range_rate'] = obj['v_lon']

        if radar_pos_data[index] and 'data' in radar_pos_data[index]:
            radar_pos_data[index]['data'].append(obj)

    if 0x471 <= cid <= 0x474:
        index = cid - 0x471
        if radar_pos_data[index] and 'data' in radar_pos_data[index]:
            for idx, obj in enumerate(radar_pos_data[index]['data']):
                if obj['id'] == r['TargetsAK_ExtraAttrib_ID'] + index * 32:
                    obj.update({'length': float(r['TargetsAK_ExtraAttrib_Length']),
                                'confdlevel': int(r['TargetsAK_ExtraAttrib_ConfdLevel']),
                                'colldetrgn': int(r['TargetsAK_ExtraAttrib_CollDetRgn']),
                                'width': float(r['TargetsAK_ExtraAttrib_CollDetRgn']),
                                'measstate': int(r['TargetsAK_ExtraAttrib_MeasState']),
                                'dyn_prop': 'dyn_prop_%03d' % int(r['TargetsAK_ExtraAttrib_MovStatus']),
                                'tgt_status': 'State_%07f' % (int(int(r['TargetsAK_ExtraAttrib_MeasState']) * 100) +int(r['TargetsAK_ExtraAttrib_ConfdLevel'])),
                                'power': int(r['TargetsAK_ExtraAttrib_SNR']),
                                'orientagl': float(r['TargetsAK_ExtraAttrib_OrientAgl']),
                                'objclass': int(r['TargetsAK_ExtraAttrib_ObjClass'])})

    if 0x481 <= cid <= 0x484:
        index = cid - 0x481
        if radar_pos_data[index]:
            radar_pos_data[index]['trackcnt'] = r['Targets_EOF_NumAK']


def parser_mu_f(cid, data, ctx=None):
    if cid not in mn_ids:
        return None
    r = mn_db.decode_message(cid, data)

    # print("0x%x" % id, r)
    if not ctx.get('mn_f_obs'):
        ctx['mn_f_obs'] = list()
    if cid == 0x4b1:
        return {'type': 'status', "status_show": [{"text": "FL_speed:{:.2f}km/h".format(r["RadarSubVehicle_Speed"]*3.6), "height": 40}]}
    elif cid == 0x4b2:
        return {'type': 'status', "status_show": [{"text": "FR_speed:{:.2f}km/h".format(r["RadarSubVehicle_Speed"]*3.6), "height": 60}]}
    else:
        return parser_mu(cid, r)


def parser_mu_r(cid, data, ctx=None):
    if cid not in mn_ids:
        return None
    r = mn_db.decode_message(cid, data)

    # print("0x%x" % id, r)
    if not ctx.get('mn_r_obs'):
        ctx['mn_r_obs'] = list()
    if cid == 0x4b3:
        return {'type': 'status', "status_show": [{"text": "RL_speed:{:.2f}km/h".format(r["RadarSubVehicle_Speed"]*3), "height": 40}]}
    elif cid == 0x4b4:
        return {'type': 'status', "status_show": [{"text": "RR_speed:{:.2f}km/h".format(r["RadarSubVehicle_Speed"]*3), "height": 60}]}
    else:
        return parser_mu(cid, r)


def parser_mu_fl(cid, data, ctx=None):
    if cid not in mn_ids:
        return None
    r = mn_db.decode_message(cid, data)

    # print("0x%x" % id, r)
    if not ctx.get('mn_f_obs'):
        ctx['mn_f_obs'] = list()
    if cid == 0x4b1:
        return {'type': 'status', "status_show": [{"text": "FL_speed:{:.2f}km/h".format(r["RadarSubVehicle_Speed"]*3.6)}]}
    else:
        return parser_mu(cid, r)


def parser_mu_fr(cid, data, ctx=None):
    if cid not in mn_ids:
        return None
    r = mn_db.decode_message(cid, data)

    # print("0x%x" % id, r)
    if not ctx.get('mn_f_obs'):
        ctx['mn_f_obs'] = list()
    if cid == 0x4b2:
        return {'type': 'status', "status_show": [{"text": "FR_speed:{:.2f}km/h".format(r["RadarSubVehicle_Speed"]*3.6)}]}
    else:
        return parser_mu(cid, r)


def parser_mu_rl(cid, data, ctx=None):
    if cid not in mn_ids:
        return None
    r = mn_db.decode_message(cid, data)

    # print("0x%x" % id, r)
    if not ctx.get('mn_r_obs'):
        ctx['mn_r_obs'] = list()
    if cid == 0x4b3:
        return {'type': 'status', "status_show": [{"text": "RL_speed:{:.2f}km/h".format(r["RadarSubVehicle_Speed"]*3.6)}]}
    else:
        return parser_mu(cid, r)


def parser_mu_rr(cid, data, ctx=None):
    if cid not in mn_ids:
        return None
    r = mn_db.decode_message(cid, data)

    # print("0x%x" % id, r)
    if not ctx.get('mn_r_obs'):
        ctx['mn_r_obs'] = list()
    if cid == 0x4b4:
        return {'type': 'status', "status_show": [{"text": "RR_speed:{:.2f}km/h".format(r["RadarSubVehicle_Speed"]*3.6)}]}
    else:
        return parser_mu(cid, r)


if __name__ == "__main__":
    parser_mu_r(0x20a, bytes().fromhex("a601ee81fb7fa080"), {})
