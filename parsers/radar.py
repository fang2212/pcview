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
# db_st24 = cantools.database.load_file('dbc/sensortech-24G.dbc', strict=False)
db_st77 = cantools.database.load_file('dbc/sensortech-77G.dbc', strict=False)
# db_mun = cantools.database.load_file('dbc/[muniu]RadarDataAnalysis.dbc', strict=False)
# db_erd = cantools.database.load_file('dbc/EMRR_CAN message parse.dbc', strict=False)

db_fusion_mrr = cantools.database.load_file('dbc/MRR_radar_CAN.dbc', strict=False)
db_sta77_2 = cantools.database.load_file('dbc/sensortech-77G.dbc', strict=False)

db_xyd2 = cantools.database.load_file('dbc/[XYD]P18006Plus_Targets_CAN_V1.3.dbc', strict=False)
db_anc = cantools.database.load_file('dbc/[AZJ]Radar51F_target.dbc', strict=False)
db_ctlrr = cantools.database.load_file('dbc/[CT]CTLRR-320_CAN_V4.dbc', strict=False)

db_vfr = cantools.database.load_file('dbc/TSMTC_VFR_MR_316.dbc', strict=False)
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
        # speed
        if 'RadarDevice_Speed' in r:
            speed_ars = r['RadarDevice_Speed'] * 3.6
            ctx['speed'] = speed_ars
        if ctx.get('radar_status') is None:
            pass
    elif id == 0x301:
        # yawrate
        if 'RadarDevice_YawRate' in r:
            yaw_rate_ars = r['RadarDevice_YawRate'] / 57.3 *(-1) # 跟车身坐标系相反
            ctx['yaw_rate'] = yaw_rate_ars
            if ctx.get('speed'):
                speed = ctx['speed']
                ctx['speed'] = []
                return {'type': 'vehicle_state', 'yaw_rate': yaw_rate_ars, 'speed': speed}

        # pass

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

        # only show ego-lane and next-lane ttc
        if fabs(y_raw) > 6.0:
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

            # ttc_a is not robust, so only use ttc_m
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


#
# erdobs = []
#
#
# def parse_erd(id, buf, ctx=None):
#     global erdobs
#     # print('0x%x' % id, r)
#     if id >= 0x500 and id <= 0x53f:
#         range = 0.01 * (buf[0] | (buf[1] & 0x7f) << 8)
#         if abs(range) > 0.1:
#             # angle=0.1*((buf[5])>>2 | ((buf[6]& 0x1f) << 6))
#             # range_acceleration=0.05*(buf[4] | (buf[5]& 0x03) << 8)
#             # range_rate=0.01*(buf[2] | (buf[3]& 0x3f) << 8)
#             # power = 0.1 * ((buf[5]) >> 5 | (buf[6] & 0x7f) << 3)
#             angle = 0.1 * ((buf[5]) >> 2 | ((buf[6] & 0x1f) << 6) - ((buf[6] & 0x1f) >> 4) * (2 ** 11))
#             range_acceleration = 0.05 * ((buf[4] | (buf[5] & 0x03) << 8) - ((buf[5] & 0x03) >> 1) * (2 ** 10))
#             range_rate = 0.01 * ((buf[2] | (buf[3] & 0x3f) << 8) - ((buf[3] & 0x3f) >> 5) * (2 ** 14))
#             power = 0.1 * ((buf[6] >> 5 | (buf[7] & 0x7f) << 3) - ((buf[7] & 0x7f) >> 6) * (2 ** 10)) - 40
#             # x, y = trans_polar2rcs(angle, range, install['erd'])
#             ret = {'type': 'obstacle', 'id': id - 0x4ff, 'range': range, 'angle': angle, 'range_rate': range_rate, 'power': power}
#             erdobs.append(ret)
#         if id == 0x53f:
#             ret = erdobs
#             erdobs = []
#             return ret
#     else:
#         return None

def parse_ctlrr(id, buf, ctx=None):
    global ctlrrobs
    ids = [m.frame_id for m in db_ctlrr.messages]
    if id not in ids:
        return None
    r = db_ctlrr.decode_message(id, buf)
    # print('0x%x' % id)
    if id == 0x710:
        range = r.get("range")
        range_rate = r.get("speed")
        angle = r.get("angle")
        tid = r.get("ID") + 200
        snr = r.get("snr")
        # x, y = trans_polar2rcs(angle, range, install['ctlrr'])
        ret = {'type': 'obstacle', 'id': tid, 'range': range, 'angle': angle, 'range_rate': range_rate, 'power': snr}
        ctlrrobs.append(ret)
    elif id == 0x6b0:
        range = (buf[1] << 5 | buf[2] >> 3) * 0.2
        range_rate = ((buf[2] & 0x07) << 8 | buf[3]) * 0.2
        if range_rate > 204.7:
            range_rate = range_rate - 409.6
        angle = (buf[4] << 2 | buf[5] >> 6) * 0.25
        if angle > 127.875:
            angle = angle - 256
        tid = buf[0]
        snr = buf[7] * 0.5
        # x, y = trans_polar2rcs(angle, range, install['ctlrr'])
        ret = {'type': 'obstacle', 'id': tid, 'range': range, 'angle': angle, 'range_rate': range_rate, 'power': snr}
        ctlrrobs.append(ret)
    elif id == 0x6a0:
        # if r.get('TRACK_RANGE')>0.01:
        #     range = r.get('TRACK_RANGE')
        #     angle = r.get('TRACK_ANGLE')
        #     range_rate = r.get('TRACK_RANGE_RATE')
        #     tid = id - 0x5FF
        #     x, y = trans_polar2rcs(angle, range, install['ctlrr'])
        #     ret = {'type': 'obstacle', 'id': tid, 'pos_lon': x, 'pos_lat': y,
        #                'range':range,'angle':angle,'range_rate':range_rate,'power': 0,'tgt_status': 'unknown','dyn_prop':'unknown','color': 1}
        #     ctlrrobs.append(ret)
        ret = ctlrrobs
        ctlrrobs = []
        return ret
    else:
        # if 'CAN_TX_VEHCILE_SPEED_CALC' in r.keys():
        #     ret={'type': 'obstacle', 'id': 0, 'pos_lon': 0, 'pos_lat': 0,
        #                'range':0,'angle':0,'range_rate':0,'power': 0,'tgt_status': 'unknown','dyn_prop':'unknown','color': 1,'speed':r.get('CAN_TX_VEHCILE_SPEED_CALC')}
        #     ctlrrobs.append(ret)
        # else:
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


st77obs_3 = []


# id 顺序 0x120 ... 0x15f 0x201
def parse_sta77_3(id, buf, ctx=None):
    global st77obs_3
    if id == 0x201:
        ret = st77obs_3
        st77obs_3 = []
        return ret
    elif not (id & 0x001):
        tid = buf[1]
        range_lon = (buf[2] << 8 | buf[3])*0.1
        range_lat = (buf[4] << 8 | buf[5])
        if range_lat > 32767:
            range_lat = (range_lat-65536)*0.1
        else:
            range_lat *= 0.1
        range = sqrt(range_lat**2+range_lon**2)
        angle = atan2(range_lat, range_lon)*180/pi
        range_rate = (buf[6] << 8 | buf[7])*0.1
        if range_lon > 0.5:
            ret = {'type': 'obstacle', 'sensor': 'sta77_3', 'sensor_type': 'radar', 'class': 'object', 'id': tid, 'range': range, 'angle': angle,
                    'range_rate': range_rate, 'pos_lat': range_lat, 'pos_lon':range_lon, 'power': 0, 'tgt_status': 'update_99','dyn_prop': 'unknown', 'color': 7}
            st77obs_3.append(ret)
        return None
    else:
        if len(st77obs_3) > 0:
            if (buf[5] << 8 | buf[6]) > 32767:
                st77obs_3[-1]['power'] = ((buf[5] << 8 | buf[6])-65536)*0.1
            else:
                st77obs_3[-1]['power'] = (buf[5] << 8 | buf[6]) * 0.1
            st77obs_3[-1]['tgt_status'] = 'update_%02d' % buf[0]
        return None


xydobs2 = []


def parse_xyd2(id, buf, ctx=None):
    global xydobs2
    ids = [m.frame_id for m in db_xyd2.messages]
    # if id == 0x301:
    #     if (buf[0] >> 7)& 0x01:
    #         speed=((buf[0] & 0x7f) << 8 | buf[1])/128.0
    #     else:
    #         speed=1000
    #     if (buf[2] >> 7)& 0x01:
    #         yaw_rate=((buf[2] & 0x7f) << 8 | buf[3])/128.0-128
    #     else:
    #         yaw_rate = 1000
    #     return {'speed':speed,'yaw_rate':yaw_rate,'type': 'obstacle', 'id': 0, 'pos_lon': 0, 'pos_lat': 0, 'range': 0, 'angle': 0,
    #            'range_rate': 0,'power':0,'dyn_prop':'Stationary','tgt_status':'lmr_state_00','color': 1}
    if id not in ids:
        return None
    r = db_xyd2.decode_message(id, buf)
    tgt_status = r.get('MMR_targetStatus')
    tgt_confidence_coef = r.get('MMR_targetConfidenceCoef')
    speed_xyd = r.get('CAN_VEHICLE_SPEED')
    if speed_xyd is not None:
        speed_xyd = speed_xyd * 3.6
    yaw_rate_xyd = r.get('CAN_YAW_RATE')
    if tgt_status is not None:
        if tgt_status == 'First detected' or (
                (tgt_status == 'unconfirmed' or tgt_status == 'valid') and tgt_confidence_coef > 30):
            range_raw = r.get('MMR_targetRange')
            angle_raw = r.get('MMR_targetAngle')
            range_rate = r.get('MMR_targetRangeRateOrig')
            power = r.get('MMR_targetPower')
            UPDATED = r.get('MMR_targetUpdated')
            if (UPDATED == 'predicted'):
                update = 0
            else:
                update = 1
            dyn_prop = r.get('MMR_targetType')
            tid = id - 0x3FF
            ret = {'type': 'obstacle', 'sensor': 'xyd2', 'sensor_type': 'radar', 'class': 'object', 'id': tid,
                   'range': range_raw, 'angle': angle_raw, 'power': power,
                   'tgt_status': tgt_status + '_%03d' % (tgt_confidence_coef) + '_%1d' % (update), 'dyn_prop': dyn_prop,
                   'color': 1}
            # x, y = trans_polar2rcs(angle, range, install['xyd2'])
            # ret = {'type': 'obstacle', 'id': tid, 'pos_lon': x, 'pos_lat': y, 'range': range, 'angle': angle,
            #        'range_rate': range_rate, 'power': power,'tgt_status': tgt_status+'_%03d'%(tgt_confidence_coef)+'_%1d'%(update),'dyn_prop':dyn_prop,'color': 1}
            xydobs2.append(ret)
        else:
            pass
            # return None
    elif speed_xyd is not None:
        # xydobs = []
        return {'type': 'vehicle_state', 'speed': speed_xyd, 'yaw_rate': yaw_rate_xyd}
        # return {'speed': speed, 'yaw_rate': yaw_rate, 'type': 'obstacle', 'id': 0, 'pos_lon': 0, 'pos_lat': 0,
        #         'range': 0, 'angle': 0,'range_rate': 0, 'power': 0, 'dyn_prop': 'Stationary', 'tgt_status': 'lmr_state_00', 'color': 1}

    if len(xydobs2) > 0 and id == 0x43F:
        ret = xydobs2
        xydobs2 = []
        return ret
    else:
        return None

# anzhijie
ancobs = []
def parse_anc(id, buf, ctx=None):
    global ancobs
    if id >= 0x500 and id < 0x520 :
        # tid = (id & 0x0FF) + 1
        r = db_anc.decode_message(id, buf)
        # range = r.get('FR_Obj%02d_Distance'%tid)
        # angle = -r.get('FR_Obj%02d_Angle'%tid)
        # range_rate = r.get('FR_Obj%02d_Speed'%tid)
        # x, y = trans_polar2rcs(angle, range, install['anc'])
        # crossrange=r.get('FR_Obj%02d_CrossRange'%tid)
        tid = r.get('TargetId')
        range = r.get('Distance')
        angle_raw = r.get('Angle')
        range_rate = r.get('Speed')
        crossrange=r.get('Cross')
        if abs(crossrange/range) < 1:
            angle = asin(crossrange/range)*180/pi
        else:
            angle = angle_raw
        # x, y = trans_polar2rcs(angle, range, install['anc'])
        ret = {'type': 'obstacle', 'sensor': 'anc', 'sensor_type': 'radar', 'class': 'object',
               'id': tid, 'range': range, 'angle': angle, 'range_rate': range_rate,
               'power': angle_raw, 'tgt_status': 'unknown', 'dyn_prop': 'unknown', 'color': 2}
        ancobs.append(ret)
        return None
    elif id == 0x520:
        ret = ancobs
        ancobs = []
        return ret
    else:
        return None


# 北京川速雷达VFR
vfr = dict()


def parse_vfr(id, buf, ctx=None):
    global vfr
    if id == 0x7d0:
        r = db_vfr.decode_message(id, buf)
        if r['FrameType'] == 0:
            vfr = dict()
            vfr['frame_id'] = r['FrameId']
            vfr['num_target'] = r['NumTarget']
            vfr['target_info'] = []
        elif r['FrameType'] == 15:
            if not 'target_info' in vfr.keys():
                return None
            tid = r['Target_Id']
            confidence = r['Target_confidence']
            x_raw = r['Target_Y']
            y_raw = r['Target_X']
            vx_raw = r['Target_Vy']
            vy_raw = r['Target_Vx']
            range = sqrt(x_raw ** 2 + y_raw ** 2)
            angle = atan2(y_raw, x_raw) * 180.0 / pi
            range_rate = sqrt(vx_raw ** 2 + vy_raw ** 2)
            ret = {'type': 'obstacle', 'sensor': 'vfr', 'sensor_type': 'radar', 'class': 'object',
                   'id': tid, 'range': range, 'angle': angle, 'range_rate': range_rate,
                   'power': confidence, 'tgt_status': 'unknown', 'dyn_prop': 'unknown', 'color': 2}
            vfr['target_info'].append(ret)
            if len(vfr['target_info']) >= vfr['num_target']:
                ret = vfr['target_info']
                vfr = dict()
                return ret
    else:
        return None