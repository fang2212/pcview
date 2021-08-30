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

cipv = {}       # Closest In Path Vehicle 路径上最近的车辆
cipp = {}
x1_lane = {}
a1j_fusion_lane = {}
detection_sensor = {
    0: 'no_matched_measurements',
    1: 'single_radar_only',
    2: 'multi_radar_only',
    3: 'vision_only',
    4: 'radar and vision',
}
vision_color = (193, 182, 255)
fusion_color = (59, 59, 238)


def parse_a1j(id, data, ctx=None):
    """
    完整的a1j数据解析，包含融合跟单目的结果
    :param id:
    :param data:
    :param ctx:
    :return:
    """
    ids = [m.frame_id for m in db_x1.messages]
    if id not in ids:
        return None
    r = db_x1.decode_message(id, data)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    # print("0x%x" % id, r)
    if not ctx.get('x1_obs'):
        ctx['x1_obs'] = list()
    if id == 0x76f:  # start of epoch
        # ctx['x1_obs'].clear()
        # cipv.clear()
        return {'type': 'vehicle_state', 'speed': r['speed']}

    elif id == 0x77f:  # frame_ped
        cipp.clear()

    elif id == 0x76d:
        # CIPV
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
            cipv['color'] = vision_color
            cipv["status_show"] = [{"text": "vision color", "height": 80, "style": vision_color, "size": 0.6}]
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
        cipv.clear()
        # return cipv

    elif 0x770 <= id <= 0x777:
        # other car
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
            x1_obs['color'] = vision_color
            x1_obs['width'] = 1.5
            x1_obs["status_show"] = [{"text": "vision color", "height": 80, "style": vision_color, "size": 0.6}]
            x1_obs_list.append(x1_obs)
            ctx['x1_obs'].append(x1_obs.copy())

    elif id == 0x77a:
        # ped cipo
        ped = None
        cipp['width'] = 0.3
        cipp['type'] = 'obstacle'
        cipp['sensor'] = 'x1'
        cipp['cipo'] = False
        cipp['id'] = r['TargetPedestrian_ID']
        cipp['vel_lon'] = r['TargetPedestrian_VelX']
        cipp['pos_lat'] = r['TargetPedestrian_PosY']
        cipp['pos_lon'] = r['TargetPedestrian_PosX']
        cipp['class'] = 'pedestrian'
        cipp['TTC'] = r['TargetPedestrian_TTC']
        if cipp['pos_lon'] > 0.0:
            ctx['x1_obs'].append(cipp.copy())

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
            x1_ped['vel_lon'] = 0
            # x1_ped['height'] = 1.6
            if x1_ped['pos_lon'] > 0:
                x1_ped_list.append(x1_ped.copy())
                ctx['x1_obs'].append(x1_ped.copy())
            # x1_ped.clear()
        if id == 0x77d:
            if ctx.get('x1_obs'):
                ret = ctx['x1_obs'].copy()
                ctx['x1_obs'].clear()
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
            x1_lane[index]['color'] = fusion_color
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
            x1_lane[index]['LineMarkColor'] = r['Lane' + '%01d' % (index + 1) + '_LineMarkColor']

            x1_lane[index]['type'] = 'lane'
            x1_lane[index]['sensor'] = 'x1'
            x1_lane[index]['id'] = index

        if id == 0x5f7:
            res = []
            for lane in x1_lane:
                res.append(x1_lane[lane])
            # res = x1_lane.copy()
            x1_lane.clear()
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
        # print("0x%x" % id, r)
        if 'fusion' not in ctx:
            return
        index = (id - 0x400) // 2
        # print(index)
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
                ctx['fusion'][index]['sensor'] = 'a1j_fusion'

                ctx['fusion'][index]['height'] = 1.5
        else:
            ctx['fusion'][index] = dict()
            ctx['fusion'][index]['color'] = fusion_color
            ctx['fusion'][index]["status_show"] = [{"text": "fusion color", "height": 160, "style": fusion_color, "size": 0.6}]
            ctx['fusion'][index]['id'] = r['TrackID_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['width'] = r['Width_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['acc_lat'] = r['Accel_lat_obj_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['status'] = r['Status_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['class'] = r['MC_object_class_' + '%02d' % (index + 1)]
            ctx['fusion'][index]['vis_track_id'] = r['Vis_Track_ID_' + '%02d' % (index + 1)]
            # ctx['fusion'][index]['confidence'] = r['Confidence_'+'%02d' % (index+1)]

            if index >= 16:
                print("fusion:", len(ctx["fusion"]))
                ret = []
                for key in ctx['fusion']:
                    if key == 255 or isinstance(key, type('')) or 'id' not in ctx['fusion'][key] or 'type' not in \
                            ctx['fusion'][key] or ctx['fusion'][key]['pos_lon'] == 0:
                        continue
                    obs = ctx['fusion'][key]
                    ret.append(obs.copy())
                return ret


def parse_a1j_fusion(id, data, ctx=None):
    """
    a1j融合数据，另外根据业务需求加了车道线解析
    :param id:
    :param data:
    :param ctx:
    :return:
    """
    ids = [m.frame_id for m in db_x1.messages]
    if id not in ids:
        return None
    r = db_x1.decode_message(id, data)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    # print("0x%x" % id, r)
    if not ctx.get('x1_obs'):
        ctx['x1_obs'] = list()

    if 0x400 <= id <= 0x41f:
        # print("0x%x" % id, r)
        if 'fusion' not in ctx:
            return
        index = (id - 0x400) // 2
        # print(index)
        if id & 1:
            if index in ctx['fusion']:
                ctx['fusion'][index]['pos_lon'] = r['L_long_rel_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['pos_lat'] = r['L_lat_rel_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['vel_lon'] = r['V_long_obj_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['vel_lat'] = r['V_lat_obj_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['acc_lon'] = r['Accel_long_obj_' + '%02d' % (index + 1)]
                ctx['fusion'][index]['TTC'] = -r['L_long_rel_' + '%02d' % (index + 1)] / r[
                    'V_long_obj_' + '%02d' % (index + 1)] if r['V_long_obj_' + '%02d' % (index + 1)] < 0 else 7.0
                ctx['fusion'][index]['detection_sensor'] = detection_sensor.get(
                    r['DetectionSensor_' + '%02d' % (index + 1)])
                ctx['fusion'][index]['cipo'] = True if id == 0x401 else False
                ctx['fusion'][index]['type'] = 'obstacle'
                ctx['fusion'][index]['sensor'] = 'x1_fusion'
                # ctx['fusion'][index]['class'] = 'fusion'
                # ctx['fusion'][index]['width'] = 1.5
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

    elif 0x5f0 <= id <= 0x5f7:
        # lane
        index = (id - 0x5f0) // 2

        if index not in a1j_fusion_lane:
            a1j_fusion_lane[index] = {}

        # lane Data A
        tmp1 = 'Lane' + '%01d' % (index + 1) + '_Type'
        if tmp1 in r:
            a1j_fusion_lane[index] = dict()
            a1j_fusion_lane[index]['Lane_Type'] = r['Lane' + '%01d' % (index + 1) + '_Type']
            a1j_fusion_lane[index]['Quality'] = r['Lane' + '%01d' % (index + 1) + '_Quality']
            a1j_fusion_lane[index]['a0'] = r['Lane' + '%01d' % (index + 1) + '_Position']
            a1j_fusion_lane[index]['a2'] = r['Lane' + '%01d' % (index + 1) + '_Curvature']
            a1j_fusion_lane[index]['a3'] = r['Lane' + '%01d' % (index + 1) + '_CurvatureDerivative']
            a1j_fusion_lane[index]['WidthMarking'] = r['Lane' + '%01d' % (index + 1) + '_WidthMarking']

        # lane Data B
        tmp1 = 'Lane' + '%01d' % (index + 1) + '_HeadingAngle'
        if tmp1 in r:
            if not a1j_fusion_lane[index]:
                return None

            a1j_fusion_lane[index]['a1'] = r['Lane' + '%01d' % (index + 1) + '_HeadingAngle']
            a1j_fusion_lane[index]['ViewRangeStart'] = r['Lane' + '%01d' % (index + 1) + '_ViewRangeStart']
            a1j_fusion_lane[index]['range'] = r['Lane' + '%01d' % (index + 1) + '_ViewRangeEnd']
            a1j_fusion_lane[index]['LineCrossing'] = r['Lane' + '%01d' % (index + 1) + '_LineCrossing']
            a1j_fusion_lane[index]['LineMarkColor'] = r['Lane' + '%01d' % (index + 1) + '_LineMarkColor']

            a1j_fusion_lane[index]['type'] = 'lane'
            a1j_fusion_lane[index]['sensor'] = 'x1'
            a1j_fusion_lane[index]['id'] = index

        if id == 0x5f7:
            res = []
            for lane in a1j_fusion_lane:
                res.append(a1j_fusion_lane[lane])
            # res = x1_lane.copy()
            a1j_fusion_lane.clear()
            # print(res)
            return res


def parse_a1j_vision(id, data, ctx=None):
    """
    a1j单目数据，另外根据业务需求加了车道线解析
    :param id:
    :param data:
    :param ctx:
    :return:
    """
    ids = [m.frame_id for m in db_x1.messages]
    if id not in ids:
        return None
    r = db_x1.decode_message(id, data)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r

    if not ctx.get('x1_obs'):
        ctx['x1_obs'] = list()
    if id == 0x76f:  # start of epoch
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
            cipv['sensor'] = 'x1'
            cipv['cipo'] = True
            cipv['id'] = r['Vehicle_ID']
            cipv['pos_lat'] = r['TargetVehicle_PosY']
            cipv['pos_lon'] = r['TargetVehicle_PosX']

            # print('X %.1f', r['TargetVehicle_PosX'])
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
        cipv.clear()
        # return cipv

    elif 0x770 <= id <= 0x777:
        # other car
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
            x1_obs['width'] = 1.5
            x1_obs_list.append(x1_obs)
            ctx['x1_obs'].append(x1_obs.copy())

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
        cipp['class'] = 'pedestrian'
        cipp['TTC'] = r['TargetPedestrian_TTC']
        if cipp['pos_lon'] > 0.0:
            ctx['x1_obs'].append(cipp.copy())

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
            x1_ped['vel_lon'] = 0
            # x1_ped['height'] = 1.6
            if x1_ped['pos_lon'] > 0:
                x1_ped_list.append(x1_ped.copy())
                ctx['x1_obs'].append(x1_ped.copy())
            # x1_ped.clear()
        if id == 0x77d:
            if ctx.get('x1_obs'):
                ret = ctx['x1_obs'].copy()
                ctx['x1_obs'].clear()
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
            x1_lane[index]['color'] = fusion_color
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
            x1_lane[index]['LineMarkColor'] = r['Lane' + '%01d' % (index + 1) + '_LineMarkColor']

            x1_lane[index]['type'] = 'lane'
            x1_lane[index]['sensor'] = 'x1'
            x1_lane[index]['id'] = index

        if id == 0x5f7:
            res = []
            for lane in x1_lane:
                res.append(x1_lane[lane])
            # res = x1_lane.copy()
            x1_lane.clear()
            # print(res)
            return res
