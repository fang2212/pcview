#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/10/10
# @Author  : Janker
# @File    : d1.py
# @Desc    :

# import time
import cantools

# db_d1 = cantools.database.load_file('dbc/MINIEYE_CAR.dbc', strict=False)
# db_d1.add_dbc_file('dbc/MINIEYE_PED.dbc')
# db_d1.add_dbc_file('dbc/MINIEYE_LANE.dbc')
db_d1 = cantools.database.load_file('dbc/minieye_debug.dbc', strict=False)
# db_d1.add_dbc_file('dbc/ESR DV3_64Tgt.dbc')

cipv = {}
cipp = {}
d1_lane = {}
spp_lane = {}


def parse_d1(id, data, ctx=None):
    ids = [m.frame_id for m in db_d1.messages]
    if id not in ids:
        return None
    r = db_d1.decode_message(id, data)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    # print("0x%x" % id, r)
    if not ctx.get('d1_obs'):
        ctx['d1_obs'] = list()

    # 车中线 int:272
    if id == 0x110:
        return {
            "type": "lane",
            "type_class": "d1_spp",
            "range": 50,
            "a0": r["COEFF_A0"],
            "a1": r["COEFF_A1"],
            "a2": r["COEFF_A2"],
            "a3": r["COEFF_A3"],
            "style": spp_lane.get("style")
        }

    # 车中线显示状态 int:796
    elif id == 0x31c:
        spp_lane["style"] = "" if r["LCK_Mode"] == 4 else "dotted"      # 正常显示为直线，否则虚线

    elif id == 0x76f:  # start of epoch
        # ctx['d1_obs'].clear()
        cipv.clear()
        return {'type': 'vehicle_state', 'speed': r['speed'] / 3.6}

    elif id == 0x77f:  # frame_ped
        cipp.clear()

    elif id == 0x76d:
        # CIPV
        if r['TargetVehicle_Type'] == 'NoVehicle':
            return None
        else:
            # print("0x%x" % id, r)
            cipv['type'] = 'obstacle'
            cipv['sensor'] = 'd1'
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

        ctx['d1_obs'].append(cipv.copy())
        # return cipv

    elif 0x770 <= id <= 0x777:
        # other car
        index = id - 0x770 + 1
        obs_num = r['AdditionVehicleNumber' + str(index)]
        d1_obs_list = []
        d1_obs = {}
        for i in range(obs_num):
            d1_obs['type'] = 'obstacle'
            d1_obs['sensor'] = 'd1'
            d1_obs['id'] = r['Vehicle' + str(2 * (index - 1) + i + 1) + '_ID']
            d1_obs['class'] = r['AdditionVehicle' + str(2 * (index - 1) + i + 1) + '_Type']
            d1_obs['pos_lon'] = r['AdditionVehicle' + str(2 * (index - 1) + i + 1) + '_PosX']
            d1_obs['pos_lat'] = r['AdditionVehicle' + str(2 * (index - 1) + i + 1) + '_PosY']
            d1_obs['ttc'] = 7
            d1_obs['vel_lon'] = 0
            d1_obs['cipv'] = False
            d1_obs['color'] = 4
            d1_obs['width'] = 1.5
            d1_obs_list.append(d1_obs)
            ctx['d1_obs'].append(d1_obs.copy())

    elif id == 0x77a:
        # ped cipo
        ped = None
        cipp['width'] = 0.3
        cipp['type'] = 'obstacle'
        cipp['sensor'] = 'd1'
        cipp['cipo'] = True
        cipp['id'] = r['TargetPedestrian_ID']
        cipp['vel_lon'] = r['TargetPedestrian_VelX']
        cipp['pos_lat'] = r['TargetPedestrian_PosY']
        cipp['pos_lon'] = r['TargetPedestrian_PosX']
        cipp['color'] = 4
        cipp['class'] = 'pedestrian'
        cipp['TTC'] = r['TargetPedestrian_TTC']
        if cipp['pos_lon'] > 0.0:
            ctx['d1_obs'].append(cipp.copy())

    elif 0x77b <= id <= 0x77d:
        # other ped
        index = id - 0x77a
        ped_num = r['AdditionPedestrianNumber' + str(index)]
        d1_ped_list = []
        d1_ped = {}
        for i in range(ped_num):
            d1_ped['width'] = 0.3
            d1_ped['cipo'] = False
            d1_ped['id'] = r['AdditionPedestrian' + str(2 * (index - 1) + i + 1) + '_ID']
            d1_ped['class'] = r['TargetPedestrian' + str(2 * (index - 1) + i + 1) + '_Type']
            d1_ped['pos_lon'] = r['AdditionPedestrian' + str(2 * (index - 1) + i + 1) + '_PosX']
            d1_ped['pos_lat'] = r['AdditionPedestrian' + str(2 * (index - 1) + i + 1) + '_PosY']
            d1_ped['type'] = 'obstacle'
            d1_ped['sensor'] = 'd1'
            d1_ped['class'] = 'pedestrian'
            d1_ped['color'] = 4
            d1_ped['vel_lon'] = 0
            # d1_ped['height'] = 1.6
            if d1_ped['pos_lon'] > 0:
                d1_ped_list.append(d1_ped.copy())
                ctx['d1_obs'].append(d1_ped.copy())
            # d1_ped.clear()
        if id == 0x77d:
            if ctx.get('d1_obs'):
                ret = ctx['d1_obs'].copy()
                ctx['d1_obs'].clear()
                return ret
    elif 0x5f0 <= id <= 0x5f7:
        # lane
        index = (id - 0x5f0) // 2

        if index not in d1_lane:
            d1_lane[index] = {}

        # lane Data A
        tmp1 = 'Lane' + '%01d' % (index + 1) + '_Type'
        if tmp1 in r:
            d1_lane[index] = dict()
            d1_lane[index]['Lane_Type'] = r['Lane' + '%01d' % (index + 1) + '_Type']
            d1_lane[index]['Quality'] = r['Lane' + '%01d' % (index + 1) + '_Quality']
            d1_lane[index]['a0'] = r['Lane' + '%01d' % (index + 1) + '_Position']
            d1_lane[index]['a2'] = r['Lane' + '%01d' % (index + 1) + '_Curvature']
            d1_lane[index]['a3'] = r['Lane' + '%01d' % (index + 1) + '_CurvatureDerivative']
            d1_lane[index]['WidthMarking'] = r['Lane' + '%01d' % (index + 1) + '_WidthMarking']

        # lane Data B
        tmp1 = 'Lane' + '%01d' % (index + 1) + '_HeadingAngle'
        if tmp1 in r:
            if not d1_lane[index]:
                return None

            d1_lane[index]['a1'] = r['Lane' + '%01d' % (index + 1) + '_HeadingAngle']
            d1_lane[index]['ViewRangeStart'] = r['Lane' + '%01d' % (index + 1) + '_ViewRangeStart']
            d1_lane[index]['range'] = r['Lane' + '%01d' % (index + 1) + '_ViewRangeEnd']
            d1_lane[index]['LineCrossing'] = r['Lane' + '%01d' % (index + 1) + '_LineCrossing']
            d1_lane[index]['LineMarkColor'] = r['Lane' + '%01d' % (index + 1) + '_LineMarkColor']

            d1_lane[index]['type'] = 'lane'
            d1_lane[index]['sensor'] = 'd1'
            d1_lane[index]['id'] = index
            d1_lane[index]['color'] = 4

        if id == 0x5f7:
            res = []
            for lane in d1_lane:
                # print(d1_lane[lane])
                res.append(d1_lane[lane])
            # res = d1_lane.copy()
            d1_lane.clear()
            # print(res)
            return res

    # fusion
    elif id == 0x420:
        ret = []
        if ctx.get('fusion'):
            for key in ctx['fusion']:
                if key == 255 or isinstance(key, type('')) or 'id' not in ctx['fusion'][key] or 'type' not in \
                        ctx['fusion'][key] or ctx['fusion'][key]['pos_lon'] == 0:
                    continue
                obs = ctx['fusion'][key]
                ret.append(obs.copy())
            ctx.pop('fusion')
            # print('fusion', ret)

        ctx['fusion'] = {}
        ctx['fusion']['frameid'] = r['FrameID']
        ctx['fusion']['counter'] = r['Counter']

        if ret:
            return ret
    elif 0x400 <= id <= 0x41f:
        if 'fusion' not in ctx:
            ctx['fusion'] = {}
            # return
        index = (id - 0x400) // 2
        if id & 1:
            if index in ctx['fusion']:
                ctx['fusion'][index]['pos_lon'] = r['L_long_rel_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['pos_lat'] = r['L_lat_rel_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['vel_lon'] = r['V_long_obj_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['vel_lat'] = r['V_lat_obj_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['acc_lon'] = r['Accel_long_obj_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['TTC'] = -r['L_long_rel_' + '%02d' % (index + 1)] / r[
                    'V_long_obj_' + '%02d' % (index + 1)] if r['V_long_obj_' + '%02d' % (index + 1)] < 0 else 7.0
                ctx['fusion'][index]['detection_sensor'] = r['DetectionSensor_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['cipo'] = True if id == 0x401 else False
                ctx['fusion'][index]['type'] = 'obstacle'
                ctx['fusion'][index]['sensor'] = 'd1_fusion'
                ctx['fusion'][index]['height'] = 1.5
        else:
            ctx['fusion'][index] = dict()
            ctx['fusion'][index]['id'] = r['TrackID_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['width'] = r['Width_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['acc_lat'] = r['Accel_lat_obj_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['status'] = r['Status_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['class'] = r['MC_object_class_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['vis_track_id'] = r['Vis_Track_ID_' + '%02d' % (index + 1)]
            # ctx['fusion'][index]['confidence'] = r['Confidence_'+'%02d' % (index+1)]

            if index >= 16:
                ret = []
                for key in ctx['fusion']:
                    if key == 255 or isinstance(key, type('')) or 'id' not in ctx['fusion'][key] or 'type' not in \
                            ctx['fusion'][key] or ctx['fusion'][key]['pos_lon'] == 0:
                        continue
                    obs = ctx['fusion'][key]
                    ret.append(obs.copy())
                return ret

        if id == 0x413:
            ret = []
            if ctx.get('fusion'):
                for key in ctx['fusion']:
                    if key == 255 or isinstance(key, type('')) or 'id' not in ctx['fusion'][key] or 'type' not in \
                            ctx['fusion'][key] or ctx['fusion'][key]['pos_lon'] == 0:
                        continue
                    obs = ctx['fusion'][key]
                    ret.append(obs.copy())
                ctx.pop('fusion')
                return ret
