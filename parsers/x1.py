#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/10/10
# @Author  : Janker
# @File    : x1.py
# @Desc    :

# import time
import cantools


# db_x1 = cantools.database.load_file('dbc/MINIEYE_CAR.dbc', strict=False)
# db_x1.add_dbc_file('dbc/MINIEYE_PED.dbc')
# db_x1.add_dbc_file('dbc/MINIEYE_LANE.dbc')
db_x1 = cantools.database.load_file('dbc/MINIEYE_fusion_CAN_V0.3_20190715.dbc', strict=False)
# db_x1.add_dbc_file('dbc/ESR DV3_64Tgt.dbc')

cipv = {}
cipp = {}


def parse_x1(id, data, ctx=None):
    ids = [m.frame_id for m in db_x1.messages]
    if id not in ids:
        return None
    r = db_x1.decode_message(id, data)
    # print("0x%x" % id, r)
    if not ctx.get('x1_obs'):
        ctx['x1_obs'] = list()
    if id == 0x76f:  # start of epoch
        # print(r)

        # print(ctx['x1_obs'])
        ctx['x1_obs'].clear()
        # x1_obs.clear()
        cipv.clear()

    elif id == 0x77f:  # frame_ped
        cipp.clear()

    elif id == 0x76d:
        # print("0x%x" % id, r)
        if r['TargetVehicle_Type'] == 'NoVehicle':
            return None
        else:
            # print("0x%x" % id, r)
            cipv['type'] = 'obstacle'
            cipv['sensor'] = 'x1'
            cipv['cipo'] = True
            cipv['id'] = r['Vehicle_ID']
            cipv['pos_lat'] = r['TargetVehicle_PosY']
            cipv['pos_lon'] = r['TargetVehicle_PosX']

            # print('X %.1f', r['TargetVehicle_PosX'])
            cipv['color'] = 4
            cipv['class'] = r['TargetVehicle_Type']
            # return {'type': 'obstacle','id': r['TargetID'], 'pos_lat': r['TargetVehiclePosY'], 'pos_lon': r['TargetVehiclePosX'], 'color': 3}
    elif id == 0x76e:
        if len(cipv) == 0:
            return None
        cipv['width'] = r['TargetVehicle_Width']
        # print('width %.1f', r['TargetVehicle_Width'])
        cipv['confi'] = r['TargetVehicle_Confidence']
        cipv['acc_lon'] = r['TargetVehicle_AccelX']
        cipv['vel_lon'] = r['TargetVehicle_VelX']
        cipv['TTC'] = r['TargetVehicle_TTC']

        ctx['x1_obs'].append(cipv.copy())
        # return cipv

    elif 0x770 <= id <= 0x777:
        index = id - 0x770 + 1
        obs_num = r['AdditionVehicleNumber' + str(index)]
        x1_obs_list = []
        x1_obs = {}
        for i in range(obs_num):
            x1_obs['type'] = 'obstacle'
            x1_obs['sensor'] = 'x1'
            x1_obs['id'] = r['Vehicle' + str(2 * (index - 1) + i + 1) + '_ID']
            x1_obs['class'] = r['AdditionVehicle' + str(2 * (index - 1) + i + 1) + '_Type']
            x1_obs['pos_lon'] = r['AdditionVehicle' + str(2 * (index - 1) + i + 1) + '_PosX']
            x1_obs['pos_lat'] = r['AdditionVehicle' + str(2 * (index - 1) + i + 1) + '_PosY']
            x1_obs['ttc'] = 7
            x1_obs['vel_lon'] = 0
            x1_obs['cipv'] = False
            x1_obs['color'] = 4
            x1_obs['width'] = 2
            x1_obs_list.append(x1_obs)
            ctx['x1_obs'].append(x1_obs.copy())

        # return x1_obs_list

    elif id == 0x77a:
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
        # cipv['height'] = 1.6
        # cipv['TTC'] = r['TTC']
        if cipp['pos_lon'] > 0.0:
            # ped = cipp.copy()
            ctx['x1_obs'].append(cipp.copy())
        # cipv.clear()
        #     return cipp

    elif 0x77b <= id <= 0x77d:
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
                ctx['x1_obs'].append(x1_ped.copy())
            # x1_ped.clear()
        if id == 0x77d:
            # pass
            # print(len(ctx['x1_obs']), ctx['x1_obs'])
            if ctx.get('x1_obs'):
                ret = ctx['x1_obs'].copy()
                ctx['x1_obs'].clear()
                return ret
        # return x1_ped_list

    if id == 0x420:
        ctx['fusion'] = {}
        ctx['fusion']['frameid'] = r['FrameID']
        ctx['fusion']['counter'] = r['Counter']

    if 0x400 <= id <= 0x41f:
        if 'fusion' not in ctx:
            return
        index = (id - 0x400) // 2
        # print(index)
        if id & 1:
            if index in ctx['fusion']:
                ctx['fusion'][index]['pos_lon'] = r['L_long_rel_'+'%02d'%(index+1)]
                ctx['fusion'][index]['pos_lat'] = r['L_lat_rel_'+'%02d'%(index+1)]
                ctx['fusion'][index]['vx'] = r['V_long_obj_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['vy'] = r['V_lat_obj_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['ax'] = r['Accel_long_obj_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['cipo'] = False
                ctx['fusion'][index]['type'] = 'obstacle'
                ctx['fusion'][index]['class'] = 'fusion_data'
                ctx['fusion'][index]['color'] = 7
                ctx['fusion'][index]['width'] = 0.15
                ctx['fusion'][index]['height'] = 0.15
        else:
            ctx['fusion'][index] = dict()
            ctx['fusion'][index]['id'] = r['TrackID_'+'%02d'%(index+1)]
            ctx['fusion'][index]['ay'] = r['Accel_lat_obj_'+'%02d'%(index+1)]

        if id == 0x41f:
            ret = []
            for key in ctx['fusion']:
                if key == 255 or type(key) == type('') or 'id' not in  ctx['fusion'][key] or 'type' not in  ctx['fusion'][key]:
                    continue
                obs = ctx['fusion'][key]
                ret.append(obs.copy())
            ctx.pop('fusion')
            # print('fusion', ret)
            return ret

