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
from tools.transform import Transform
from math import pi

# from config.config import install

R2D = 180.0 / pi

db_esr = cantools.database.load_file('dbc/ESR DV3_64Tgt.dbc', strict=False)
db_ars = cantools.database.load_file('dbc/ARS408.dbc', strict=False)
# db_huayu = cantools.database.load_file('/home/nan/workshop/doc/华域/lrr10_1.dbc', strict=False)

db_mrr = cantools.database.load_file('dbc/bosch_mrr_output.dbc', strict=False)
db_lmr = cantools.database.load_file('dbc/HETLMR.dbc', strict=False)
db_hmb = cantools.database.load_file('dbc/szhmb.dbc', strict=False)
db_fusion_mrr = cantools.database.load_file('dbc/MRR_radar_CAN.dbc', strict=False)
db_sta77_2 = cantools.database.load_file('dbc/sensortech-77G.dbc', strict=False)

# trans_polar2rcs = Transform().trans_polar2rcs

ars_filter = CIPOFilter()


def parse_ars(id, buf, ctx=None):
    ids = [m.frame_id for m in db_ars.messages]
    if id not in ids:
        return None
    r = db_ars.decode_message(id, buf)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    # print('0x%x' % id, r)
    if id == 0x300:  # end of scan
        # if ctx.get('ars_obj'):
        #     ret = ars_filter.add_cipo(ctx['ars_obj'])
        #     print(ret)
        #     return ret
        if ctx.get('radar_status') is None:
            pass

    elif id == 0x60a:  # new start of scan
        # print('start of scan')
        ret = None
        if ctx.get('ars_obj'):
            ret = ars_filter.add_cipo(ctx['ars_obj'].copy())
            # print(ret)
            # return ret
        ctx['ars_obj'] = []

        if ret:
            return ret

    elif id == 0x301:
        pass

    elif id == 0x60b:
        tid = r['Obj_ID']
        x_raw = r['Obj_DistLong']
        y_raw = r['Obj_DistLat']
        vx = r['Obj_VrelLong']
        vy = r['Obj_VrelLat']
        rcs = r['Obj_RCS']
        ttc = x_raw / -vx if vx < 0 else 7
        if ttc > 7:
            ttc = 7
        range = sqrt(x_raw ** 2 + y_raw ** 2)
        angle = atan2(y_raw, x_raw) * 180.0 / pi
        # x, y = trans_polar2rcs(angle, range, install['ars'])
        ret = {'type': 'obstacle', 'sensor_type': 'radar', 'id': tid, 'range': range, 'angle': angle, 'pos_lat': y_raw,
               'pos_lon': x_raw, 'vel_lat': vy, 'vel_lon': vx, 'RCS': rcs, 'TTC': ttc}
        if ctx.get('ars_obj') is not None:
            ctx['ars_obj'].append(ret.copy())
        # return ret

    elif id == 0x600:
        cluster_near_num = r['Cluster_NofClustersNear']
        cluster_far_num = r['Cluster_NofClustersFar']
        pass

    elif id == 0x701:
        tid = r['Cluster_ID']
        x_raw = r['Cluster_DistLong']
        y_raw = -1 * r['Cluster_DistLat']  # clster模式和object模式坐标系横轴是反的？
        range = sqrt(x_raw ** 2 + y_raw ** 2)
        angle = atan2(y_raw, x_raw) * 180.0 / pi
        # x, y = trans_polar2rcs(angle, range, install['ars'])
        ret = {'type': 'obstacle', 'sensor_type': 'radar', 'id': tid, 'range': range, 'angle': angle, 'color': 2}
        return ret


def parse_esr(id, buf, ctx=None):
    global esrobs
    ids = [m.frame_id for m in db_esr.messages]
    if id not in ids:
        return None
    r = db_esr.decode_message(id, buf)
    if ctx.get('parser_mode') == 'direct':
        return r
    # print('hahaha', ctx)
    if ctx is not None and not ctx.get('filter'):
        ctx['filter'] = CIPOFilter()
    if ctx is not None and not ctx.get('obs'):
        ctx['obs'] = []
    # esrobs = ctx['obs']
    # esr_filter = ctx['filter']
    # print('0x%x' % id, r)
    tgt_status = r.get('CAN_TX_TRACK_STATUS')
    if tgt_status is not None:
        if tgt_status == 'Updated_Target' or tgt_status == 'Coasted_Target' \
                or tgt_status == 'New_Target' or tgt_status == 'New_Updated_Target':
            range_raw = r.get('CAN_TX_TRACK_RANGE')
            angle_raw = r.get('CAN_TX_TRACK_ANGLE')
            tid = id - 0x500

            range_rate = r.get('CAN_TX_TRACK_RANGE_RATE')
            range_acc = r.get('CAN_TX_TRACK_RANGE_ACCEL')
            # x, y = trans_polar2rcs(angle_raw, range_raw, 'esr')
            # angle_new = atan2(y, x)*R2D
            # range_new = sqrt(x * x + y * y)

            # -YJ- new
            # v_x = range_rate * cos(angle_new/R2D)
            v_x = range_rate * cos(angle_raw / R2D)

            # ttc_m
            if range_rate < -0.1:
                ttc_m = -range_raw / range_rate
                if ttc_m > 7:
                    ttc_m = 7
            else:
                ttc_m = 7

            # ttc_a
            # t1 = v_x * v_x - 2 * range_acc * range_new
            t1 = v_x * v_x - 2 * range_acc * range_raw
            if t1 > 0 and range_acc < 0:
                # only use ttc_a when a < 0
                ttc_a = (-v_x - sqrt(t1)) / range_acc
                if ttc_a > 7:
                    ttc_a = 7
            else:
                ttc_a = 7

            if range_acc < 0:
                ttc = ttc_a
            else:
                ttc = ttc_m

            # only show ego-lane and next-lane ttc
            # if fabs(y) > 6.0:
            #     ttc = 7

            # print('ESR 0x%x' % id, r)
            # ret = {'type': 'obstacle', 'sensor': 'radar', 'class': 'object', 'id': tid, 'range': range, 'angle': angle,
            #        'color': 1}
            ret = {'type': 'obstacle', 'sensor': 'esr', 'sensor_type': 'radar', 'class': 'object', 'id': tid,
                   'range': range_raw, 'angle': angle_raw,
                   'range_rate': range_rate, 'TTC': ttc, 'TTC_m': ttc_m, 'TTC_a': ttc_a, 'color': 1}
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
    elif id == 0x4E0:
        # speed
        if 'CAN_TX_VEHICLE_SPEED_CALC' in r:
            speed_esr = r['CAN_TX_VEHICLE_SPEED_CALC'] * 3.6
            yaw_rate_esr = r['CAN_TX_YAW_RATE_CALC'] / 57.3
            # print('speed: %.1f km/h %.4f' % (speed_esr, yaw_rate_esr))
            return {'type': 'vehicle_state', 'speed': speed_esr, 'yaw_rate': yaw_rate_esr}


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
            return {'type': 'obstacle', 'sensor': 'mrr', 'sensor_type': 'radar', 'id': oid, 'pos_lon': x, 'pos_lat': y,
                    'color': 1}
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
            return {'type': 'obstacle', 'sensor': 'lmr', 'sensor_type': 'radar', 'id': id - 0x500, 'range': range,
                    'angle': angle, 'color': 2}
    return None


def parse_hmb(id, buf, ctx=None):
    # print('0x%x' % id)
    ids = [m.frame_id for m in db_hmb.messages]
    if id not in ids:
        return None

    r = db_hmb.decode_message(id, buf)
    range = r.get('Range')
    angle = -r.get('Angle')
    # x = cos(angle * pi / 180.0) * range
    # y = sin(angle * pi / 180.0) * range
    # x, y = trans_polar2rcs(angle, range, install['hmb'])
    # print("hmb radar frame")
    result = {'type': 'obstacle', 'sensor': 'hmb', 'sensor_type': 'radar', 'id': id - 0x500, 'range': range,
              'angle': angle, 'color': 4}
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
        snr = r['CAN_SNR_LEVEL' + sf]
        scan_idx = r['CAN_SCAN_INDEX_2LSB' + sf]
        amp = r['CAN_DET_AMPLITUDE' + sf]
        valid = r['CAN_DET_VALID_LEVEL' + sf]
        range_rate = r['CAN_DET_RANGE_RATE' + sf]
        host_veh_clutter = r['CAN_DET_HOST_VEH_CLUTTER' + sf]
        nd_target = r['CAN_DET_ND_TARGET' + sf]
        spres_target = r['CAN_DET_SUPER_RES_TARGET' + sf]
        # print(host_veh_clutter, nd_target, spres_target)

        result = {'type': 'obstacle', 'sensor': 'mrr_fusion', 'sensor_type': 'radar', 'id': idx, 'range': range,
                  'angle': angle, 'color': 5,
                  'snr': snr,
                  'scan_idx': scan_idx, 'amp': amp, 'valid': valid, 'range_rate': range_rate, 'super_res': spres_target}
        # if snr in ['High']:
        # print(result)
        if valid:
            return result


st77obs = []


def parse_sta77(id, buf, ctx=None):
    global st77obs
    ids = [m.frame_id for m in db_sta77_2.messages]
    if id not in ids:
        return None

    if ctx is not None and not ctx.get('filter'):
        ctx['filter'] = CIPOFilter()

    r = db_sta77_2.decode_message(id, buf)
    # print('0x%x' % id)
    id = (id & 0x000FFF00) >> 8
    if id == 0x200:
        if r.get('Fault_Level') > 0:
            print('Fault_Level:', r.get('Fault_Level'))
        ret = st77obs
        ret = ctx['filter'].add_cipo(ret)
        st77obs = []
        return ret
    elif not (id & 0x001):
        tid = ((id & 0x0FE) >> 1) + 1
        if 'Object_Number_%d' % tid in r.keys():
            range_lon = r.get('Distance_Object_%d' % tid) * 0.1
            range_lat = r.get('Cross_Object_%d' % tid) * 0.1
            # range, angle = trans_polar2rcs(range_lon, range_lat)
            range = sqrt(range_lat ** 2 + range_lon ** 2)
            angle = atan2(range_lat, range_lon) * 180 / pi
            range_rate = r.get('Relative_Object_%d' % tid) * 0.1
            # x, y = trans_polar2rcs(angle, range, install['sta77'])
            ret = {'type': 'obstacle', 'sensor': 'sta77', 'sensor_type': 'radar', 'class': 'object', 'id': tid,
                   'range': range, 'angle': angle,
                   'range_rate': range_rate, 'color': 7}
            st77obs.append(ret)
            return None
    else:  # st77obs[-1]['id']==(((id&0x0FE)>>1)+1):
        tid = ((id & 0x0FE) >> 1) + 1
        if isinstance(r.get('Amplitude_%d' % tid), (int, float)):
            st77obs[-1]['power'] = r.get('Amplitude_%d' % tid) * 0.1
            st77obs[-1]['tgt_status'] = 'SNR_%02d' % r.get('SNR_%d' % tid)
            return None
        else:
            return None
