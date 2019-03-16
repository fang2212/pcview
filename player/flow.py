import os
import cv2
import datetime
import numpy as np
from .ui import BaseDraw, CVColor, DrawParameters, DrawPed, DrawVehicle, \
                VehicleType
from math import isnan


class FlowPlayer(object):
    @classmethod
    def draw(cls, mess, img):

        speed, fps = 0, '-'
        if 'env' in mess:
            title = 'env'

            if 'speed' in mess:
                speed = "%.1f" % (3.6*float(mess['speed']))

            if 'fps' in mess['env']:
                fps = mess['env']['fps']
            t1 = datetime.datetime.now().strftime('%Y-%m-%d')
            t2 = datetime.datetime.now().strftime('%H:%M:%S')
            para_list = [
                'fps:' + str(fps),
                'speed:' + str(speed)+'km/h',
                'fid:' + str(mess.get('frame_id')),
                '' + str(t1),
                '' + str(t2)
            ]
            BaseDraw.draw_single_info(img, (0, 0), 140, title, para_list)
        # speed = float(mess['speed'])
        deviate_state = -1

        pcw_on, ped_on = '-', '-'
        ped_show = False
        if 'pcw_on' in mess:
            pcw_on = str(mess['pcw_on'])
            ped_show = True
        if 'ped_on' in mess:
            ped_on = str(mess['ped_on'])
            ped_show = True
        para_list = [
            'ped_on:' + ped_on,
            'pcw_on:' + pcw_on
        ]
        if ped_show:
            BaseDraw.draw_single_info(img, (270, 0), 120, 'ped', para_list)

        if 'pedestrians' in mess:
            res_list = mess['pedestrians']
            for i, obj in enumerate(res_list):
                BaseDraw.draw_obj_rect(img, obj['detect_box'], CVColor.Cyan)
                pos = obj['regressed_box']
                color = CVColor.Pink if obj['is_key'] else CVColor.Green
                BaseDraw.draw_obj_rect_corn(img, pos, color, 2)
                para_list = [
                    'dist:'+"%.2f" % obj['dist'],
                    'ttc:'+"%.2f" % obj['ttc'],
                    'classify_type:'+str(obj['classify_type']),
                    'type_conf:'+str(obj['type_conf']),
                    'world_x:'+"%.2f" % obj['world_x'],
                    'world_y:'+"%.2f" % obj['world_y'],
                    'type_conf:'+str(obj['type_conf']),
                    'is_danger:'+str(obj['is_danger']),
                    'is_key:'+str(obj['is_key']),
                    'predicted:'+str(obj['predicted']),
                    'id:'+str(obj['id'])
                ]
                BaseDraw.draw_head_info(img, pos[0:2], para_list, 150)

        if 'ldwparams' in mess:
            data = mess['ldwparams']
            deviate_state = int(data['deviate_state'])
            for key in data:
                if key.find('deviate') != -1:
                    data[key] = str(data[key])
                elif key.find('frame_id') == -1:
                    data[key] = "%.2f" % data[key]
            para_list = [
                "latest_dist:"+data["latest_dist"],
                "lateral_speed:"+data["lateral_speed"],
                "earliest_dist:"+data["earliest_dist"],
                "deviate_state:"+data["deviate_state"],
                "deviate_trend:"+data["deviate_trend"],
                "lt_wheel_dist:"+data["left_wheel_dist"],
                "rt_wheel_dist:"+data["right_wheel_dist"],
                "warning_dist:"+data["warning_dist"]
            ]
            BaseDraw.draw_single_info(img, (390, 0), 180, 'lane', para_list)

        if 'vehicle_warning' in mess:
            data = mess['vehicle_warning']
            vid, headway, fcw, hw, vb, ttc = '-', '-', '-', '-', '-', '-'

            vid = data['vehicle_id']
            headway = '%.2f' % data['headway']
            fcw = data['fcw']
            # ttc = data['ttc']
            hw = data['headway_warning']
            vb = data['vb_warning']
            title = 'vehicle'
            para_list = [
                'vid:' + str(vid),
                'headway:' + str(headway),
                #'ttc:' + str(ttc),
                'fcw:' + str(fcw),
                'hw:' + str(hw),
                'vb:' + str(vb)
            ]
            BaseDraw.draw_single_info(img, (140, 0), 130, title, para_list)

        if 'vehicle_measure_res_list' in mess:
            res_list = mess['vehicle_measure_res_list']
            for i, vehicle in enumerate(res_list):
                BaseDraw.draw_obj_rect(img, vehicle['det_rect'], CVColor.Cyan)
                pos = vehicle['reg_rect']
                color = CVColor.Red if vehicle['is_crucial'] else CVColor.Blue
                BaseDraw.draw_obj_rect_corn(img, pos, color, 2)
                
                vid = vehicle['vehicle_id']
                d1 = vehicle['longitude_dist']
                d2 = vehicle['lateral_dist']
                d1 = 'nan' if isnan(d1) else int(float(d1) * 100) / 100
                d2 = 'nan' if isnan(d2) else int(float(d2) * 100) / 100
                tid = str(vehicle['vehicle_class'])
                para_list = [
                    'v:'+str(d1),
                    'h:'+str(d2),
                    'type:'+str(VehicleType.get(tid)),
                    'vid:'+str(vid)
                ]
                BaseDraw.draw_head_info(img, pos[0:2], para_list, 80)

        if 'lane' in mess:
            data = mess['lane']
            BaseDraw.draw_lane_lines(img, data, 222, deviate_state, draw_all=False, speed_limit=0)
            '''
            for lane in data:
                if True:
                    width = lane['width']
                    l_type = lane['type']
                    conf = lane['confidence']
                    index = lane['label']
                    begin = int(lane['end'][1])
                    end = int(lane['start'][1])
                    if end > 720:
                        end = 720
                    color = CVColor.Blue
                    BaseDraw.draw_lane_line(img, lane['perspective_view_poly_coeff'],
                                            0.2, color, begin, end) 
            '''
        return img

    @classmethod
    def draw_vehicle_info(cls, img, position, vertical_dis, horizontal_dis, vehicle_width, vehicle_type):
        """绘制车辆信息
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            vertical_dis: float 与检测车辆的竖直距离
            horizontal_dis: float 与检测车辆的水平距离
            vehicle_width: float 检测车辆的宽度
            vehicle: str 车辆类型，见const_type
        """
        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        origin_x = max(0, x2 - 150)
        origin_y = max(0, y1 - 30)
        BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 150, 30), 0.6)
        size = 1
        BaseDraw.draw_text(img, str(vehicle_type), (x2 - 150, y1 - 5),
                           size, CVColor.White, 1)

        d1 = 'nan' if isnan(vertical_dis) else int(float(vertical_dis) * 100) / 100
        d2 = 'nan' if isnan(horizontal_dis) else int(float(horizontal_dis) * 100) / 100
        data = str(d1) + ',' + str(d2)
        BaseDraw.draw_text(img, data, (x2 - 120, y1 - 5), size, CVColor.White, 1)
