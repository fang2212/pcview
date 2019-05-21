#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/07/15
# @Author  : simon.xu
# @File    : radar.py
# @Desc    :

import cantools

from tools.match import *
from math import pi

# from utils.transform import *

# M_PI = 3.141592653589793238462643383279503

db_esr = cantools.database.load_file('dbc/ESR DV3_64Tgt.dbc', strict=False)
# db_ars = cantools.database.load_file('dbc/ARS408.dbc', strict=False)
# db_huayu = cantools.database.load_file('/home/nan/workshop/doc/华域/lrr10_1.dbc', strict=False)

db_mrr = cantools.database.load_file('dbc/bosch_mrr_output.dbc', strict=False)
db_lmr = cantools.database.load_file('dbc/HETLMR.dbc', strict=False)
db_hmb = cantools.database.load_file('dbc/szhmb.dbc', strict=False)
db_fusion_mrr = cantools.database.load_file('dbc/MRR_radar_CAN.dbc', strict=False)


# def parse_ars(id, buf, ctx=None):
#     ids = [m.frame_id for m in db_ars.messages]
#     if id not in ids:
#         return None
#     r = db_ars.decode_message(id, buf)
#     # print('0x%x' % id, r)
#     if id == 0x300:
#         if ctx.get('radar_status') is None:
#             pass
#
#     if id == 0x60b:
#         tid = r['Obj_ID']
#         x = r['Obj_DistLong']
#         y = r['Obj_DistLat']
#         ret = {'type': 'obstacle', 'sensor': 'radar', 'id': tid, 'pos_lon': x, 'pos_lat': y, 'color': 2}
#         return ret


def parse_esr(id, buf, ctx=None):
    global esrobs
    ids = [m.frame_id for m in db_esr.messages]
    if id not in ids:
        return None
    r = db_esr.decode_message(id, buf)
    # print('hahaha', ctx)
    if ctx is not None and not ctx.get('filter'):
        ctx['filter'] = CIPOFilter()
    if ctx is not None and not ctx.get('obs'):
        ctx['obs'] = []
    # esrobs = ctx['obs']
    # esr_filter = ctx['filter']
    # print('0x%x' % id)
    tgt_status = r.get('CAN_TX_TRACK_STATUS')
    if tgt_status is not None:
        if tgt_status == 'Updated_Target' or tgt_status == 'Coasted_Target' \
                or tgt_status == 'New_Target' or tgt_status == 'New_Updated_Target':
            range = r.get('CAN_TX_TRACK_RANGE')
            angle = r.get('CAN_TX_TRACK_ANGLE')
            tid = id - 0x500
            # x = cos(angle * pi / 180.0) * range + 1.64
            # y = sin(angle * pi / 180.0) * range - 0.4
            # x, y = trans_polar2rcs(angle, range, install['esr'])
            # print('ESR 0x%x' % id, r)
            ret = {'type': 'obstacle', 'sensor': 'radar', 'class': 'object', 'id': tid, 'range': range, 'angle': angle,
                   'color': 1}
            ctx['obs'].append(ret)
            # if esr_filter.update(ret):
            #     ret['cipo'] = True
            # return ret
        else:
            # print('ESR 0x%x' % id, r)
            pass
    elif 'CAN_TX_MAXIMUM_TRACKS_ACK' in r:
        # print(r['CAN_TX_MAXIMUM_TRACKS_ACK'])
        pass
    elif id == 0x540:
        idx = r['CAN_TX_TRACK_CAN_ID_GROUP']
        # print('esr 0x540')
        if idx == 0:
            ret = ctx['filter'].add_cipo(ctx['obs'])
            ctx['obs'] = []
            # print('esr', ret)
            return ret
    elif id == 0x4e3:
        # print('0x%x' % id)
        # print('0x%x' % id, r)
        pass


def parse_bosch_mrr(id, buf, ctx=None):
    ids = [m.frame_id for m in db_mrr.messages]
    if id not in ids:
        return None
    if 0x660 <= id <= 0x67f:
        idx = id - 0x660

        r = db_mrr.decode_message(id, buf)
        oid = r['X_Object{:02d}_ID'.format(idx)]
        x = r['X_Object{:02d}_dx'.format(idx)]
        y = -r['X_Object{:02d}_dy'.format(idx)]
        idx = id - 0x660
        if r['X_Object%02d_wExist' % idx] > 0.0:
            # print('0x%x' % id, r)
            return {'type': 'obstacle', 'sensor': 'radar', 'id': oid, 'pos_lon': x, 'pos_lat': y, 'color': 1}
    elif id == 0x680:
        r = db_mrr.decode_message(id, buf)
        # print('0x%x' % id, r)
        pass

    return None


def parse_hawkeye_lmr(id, buf, ctx=None):
    ids = [m.frame_id for m in db_lmr.messages]
    if id not in ids:
        return None
    r = db_lmr.decode_message(id, buf)
    # print('0x%x' % id, r)
    if 'CANTX_TargetSNR' in r:
        if r['CANTX_TargetSNR'] > 0:
            # print('0x%x' % id, r)
            range = r.get('CANTX_TragetRange')
            angle = r.get('CANTX_TargetAzimuth')
            # x = cos(angle * pi / 180.0) * range
            # y = sin(angle * pi / 180.0) * range
            # x, y = trans_polar2rcs(angle, range, install['lmr'])
            return {'type': 'obstacle', 'sensor': 'radar', 'id': id - 0x500, 'range': range, 'angle': angle, 'color': 2}

    return None


def parse_hmb(id, buf, ctx=None):
    # print('0x%x' % id)
    ids = [m.frame_id for m in db_hmb.messages]
    if id not in ids:
        return None

    r = db_hmb.decode_message(id, buf)

    # if r['Range'] :
    #     return

    range = r.get('Range')
    angle = -r.get('Angle')
    # x = cos(angle * pi / 180.0) * range
    # y = sin(angle * pi / 180.0) * range
    # x, y = trans_polar2rcs(angle, range, install['hmb'])

    # print("hmb radar frame")
    result = {'type': 'obstacle', 'sensor': 'radar', 'id': id - 0x500, 'range': range, 'angle': angle, 'color': 4}
    print(result)
    return result


def parse_fusion_mrr(id, buf, ctx=None):
    # print('0x%x' % id)
    ids = [m.frame_id for m in db_fusion_mrr.messages]
    if id not in ids:
        return None

    r = db_fusion_mrr.decode_message(id, buf)
    # print('0x%x' % id, r)

    if 0x120 <= id <= 0x15f:
        idx = id - 0x120
        sf = '_{:02d}'.format(idx + 1)
        angle = r['CAN_DET_AZIMUTH' + sf] * 180.0 / pi
        range = r['CAN_DET_RANGE' + sf]
        # x, y = trans_polar2rcs(angle, range)
        snr = r['CAN_SNR_LEVEL'+sf]
        scan_idx = r['CAN_SCAN_INDEX_2LSB'+sf]
        amp = r['CAN_DET_AMPLITUDE'+sf]
        valid = r['CAN_DET_VALID_LEVEL'+sf]
        range_rate = r['CAN_DET_RANGE_RATE'+sf]
        host_veh_clutter = r['CAN_DET_HOST_VEH_CLUTTER'+sf]
        nd_target = r['CAN_DET_ND_TARGET'+sf]
        spres_target = r['CAN_DET_SUPER_RES_TARGET'+sf]
        # print(host_veh_clutter, nd_target, spres_target)

        result = {'type': 'obstacle', 'sensor': 'radar', 'id': idx, 'range': range, 'angle': angle, 'color': 5,
                  'snr': snr,
                  'scan_idx': scan_idx, 'amp': amp, 'valid': valid, 'range_rate': range_rate, 'super_res': spres_target}
        # if snr in ['High']:
        # print(result)
        if valid:
            return result
