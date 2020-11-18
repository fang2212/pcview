#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2020/08/14
# @Author  : simon.hsu
# @File    : x1j.py
# @Desc    : x1 for JAC

# import time
import cantools

# db_x1 = cantools.database.load_file('dbc/MINIEYE_CAR.dbc', strict=False)
# db_x1.add_dbc_file('dbc/MINIEYE_PED.dbc')
# db_x1.add_dbc_file('dbc/MINIEYE_LANE.dbc')
db_x1j = cantools.database.load_file('dbc/X1_AEB_20200812.dbc', strict=False)

cipv = {}
cipp = {}
x1_lane = {}


def parse_x1j(id, data, ctx=None):
    ids = [m.frame_id for m in db_x1j.messages]
    if id not in ids:
        return None
    r = db_x1j.decode_message(id, data)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    # print("0x%x" % id, r)
    if not ctx.get('x1j_obs'):
        ctx['x1j_obs'] = list()
    if id == 0x76f:  # start of epoch
        ctx['x1j_obs'].clear()
        cipv.clear()

    elif id == 0x77f:  # frame_ped
        cipp.clear()

    elif id == 0x76d:
        # CIPV
        if r['TargetVehicle_Type'] == 'NoVehicle':
            # print(r)
            return None
        else:
            # print("0x%x" % id, r)
            cipv['type'] = 'obstacle'
            cipv['sensor'] = 'x1'
            cipv['cipo'] = True
            cipv['id'] = r['Vehicle_ID']
            cipv['pos_lat'] = r['TargetVehicle_PosY']
            cipv['pos_lon'] = r['TargetVehicle_PosX']
            cipv['width'] = r['TargetVehicle_Width']

            # print('X %.1f', r['TargetVehicle_PosX'])
            cipv['color'] = 4
            cipv['class'] = r['TargetVehicle_Type']
            # return {'type': 'obstacle','id': r['TargetID'], 'pos_lat': r['TargetVehiclePosY'], 'pos_lon': r['TargetVehiclePosX'], 'color': 3}
    elif id == 0x76e:
        if len(cipv) == 0:
            return None
        # cipv['width'] = r['TargetVehicle_Width']
        cipv['width'] = 1.5
        # print('width %.1f', r['TargetVehicle_Width'])
        cipv['confi'] = r['TargetVehicle_Confidence']
        cipv['acc_lon'] = r['TargetVehicle_AccelX']
        cipv['vel_lon'] = r['TargetVehicle_VelX']
        cipv['vel_lat'] = r['TargetVehicle_VelY']
        cipv['TTC'] = r['TargetVehicle_TTC']

        ctx['x1j_obs'].append(cipv.copy())
        # print(cipv)
        # return cipv

    elif 0x770 <= id <= 0x777:
        # other car
        index = id - 0x770 + 1
        # obs_num = r['Addition_Vehicle_Number_' + str(index)]
        # x1_obs_list = []
        x1j_obs = {}
        suffix = 'AdditionVehicle' + str(index)
        x1j_obs['type'] = 'obstacle'
        x1j_obs['sensor'] = 'x1'
        x1j_obs['id'] = r['Vehicle' + str(index) + '_ID']
        x1j_obs['class'] = r[suffix + '_Type']
        x1j_obs['pos_lon'] = r[suffix + '_PosX']
        x1j_obs['pos_lat'] = r[suffix + '_PosY']
        x1j_obs['vel_lon'] = r[suffix + '_VelX']
        x1j_obs['vel_lat'] = r[suffix + '_VelY']
        x1j_obs['status'] = r[suffix + '_Status']

        x1j_obs['ttc'] = 7
        x1j_obs['vel_lon'] = 0
        x1j_obs['cipv'] = False
        # x1j_obs['color'] = 4
        x1j_obs['width'] = 1.5

        # x1_obs_list.append(x1_obs)
        # print(x1j_obs['status'])
        # if x1j_obs['status'] == 'invalid target':
        #     return
        if x1j_obs['pos_lon'] > 0.0:
            ctx['x1j_obs'].append(x1j_obs.copy())
        # else:
        #     print(x1j_obs)

    elif id == 0x77a:
        # ped cipo
        ped = None
        cipp['width'] = 0.3
        cipp['type'] = 'obstacle'
        cipp['sensor'] = 'x1'
        cipp['cipo'] = True
        cipp['id'] = r['TargetPedestrian_ID']
        cipp['vel_lon'] = r['TargetPedestrian_VelX']
        cipp['pos_lat'] = r['TargetPedestrian_PosY']
        cipp['pos_lon'] = r['TargetPedestrian_PosX']
        cipp['color'] = 4
        cipp['class'] = 'pedestrian'
        cipp['TTC'] = r['TargetPedestrian_TTC']
        if cipp['pos_lon'] > 0.0:
            ctx['x1j_obs'].append(cipp.copy())

    elif 0x77b <= id <= 0x77d:
        # other ped
        index = id - 0x77a
        ped_num = r['AdditionPedestrianNumber' + str(index)]
        x1_ped_list = []
        x1_ped = {}
        for i in range(ped_num):
            x1_ped['width'] = 0.3
            x1_ped['cipo'] = False
            x1_ped['id'] = r['AdditionPedestrian' + str(2 * (index - 1) + i + 1) + '_ID']
            x1_ped['class'] = r['TargetPedestrian' + str(2 * (index - 1) + i + 1) + '_Type']
            x1_ped['pos_lon'] = r['AdditionPedestrian' + str(2 * (index - 1) + i + 1) + '_PosX']
            x1_ped['pos_lat'] = r['AdditionPedestrian' + str(2 * (index - 1) + i + 1) + '_PosY']
            x1_ped['type'] = 'obstacle'
            x1_ped['sensor'] = 'x1'
            x1_ped['class'] = 'pedestrian'
            x1_ped['color'] = 4
            x1_ped['vel_lon'] = 0
            # x1_ped['height'] = 1.6
            if x1_ped['pos_lon'] > 0:
                x1_ped_list.append(x1_ped.copy())
                ctx['x1j_obs'].append(x1_ped.copy())
            # x1_ped.clear()
        if id == 0x77d:
            if ctx.get('x1j_obs'):
                ret = ctx['x1j_obs'].copy()
                ctx['x1j_obs'].clear()
                return ret
    elif 0x5f0 <= id <= 0x5f7:
        # lane
        index = (id - 0x5f0) // 2

        if index not in x1_lane:
            x1_lane[index] = {}

        # lane Data A
        tmp1 = 'Lane' + '%01d' % (index + 1) + '_Type'
        if tmp1 in r:
            x1_lane[index] = dict()
            x1_lane[index]['Lane_Type'] = r['Lane' + '%01d' % (index + 1) + '_Type']
            x1_lane[index]['Quality'] = r['Lane' + '%01d' % (index + 1) + '_Quality']
            x1_lane[index]['a0'] = r['Lane' + '%01d' % (index + 1) + '_Position']
            x1_lane[index]['a2'] = r['Lane' + '%01d' % (index + 1) + '_Curvature']
            x1_lane[index]['a3'] = r['Lane' + '%01d' % (index + 1) + '_CurvatureDerivative']
            x1_lane[index]['WidthMarking'] = r['Lane' + '%01d' % (index + 1) + '_WidthMarking']

        # lane Data B
        tmp1 = 'Lane' + '%01d' % (index + 1) + '_HeadingAngle'
        if tmp1 in r:
            if not x1_lane[index]:
                return None

            x1_lane[index]['a1'] = r['Lane' + '%01d' % (index + 1) + '_HeadingAngle']
            x1_lane[index]['ViewRangeStart'] = r['Lane' + '%01d' % (index + 1) + '_ViewRangeStart']
            x1_lane[index]['range'] = r['Lane' + '%01d' % (index + 1) + '_ViewRangeEnd']
            x1_lane[index]['LineCrossing'] = r['Lane' + '%01d' % (index + 1) + '_LineCrossing']
            # x1_lane[index]['LineMarkColor'] = r['Lane' + '%01d' % (index + 1) + '_LineMarkColor']

            x1_lane[index]['type'] = 'lane'
            x1_lane[index]['sensor'] = 'x1'
            x1_lane[index]['id'] = index
            x1_lane[index]['color'] = 4

        if id == 0x5f7:
            res = []
            for lane in x1_lane:
                res.append(x1_lane[lane])
            # res = x1_lane.copy()
            x1_lane.clear()
            # print(res)
            return res

    elif id == 0x700:  # adas out
        res = {}
        res['type'] = 'hmi'
        res['sound_type'] = r['Sound_type']
        res['time_indicator'] = r['Time_Indicator']
        res['hmw_valid'] = r['HMW_valid']


