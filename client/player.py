import os
import cv2
import datetime
import numpy as np
from ui import BaseDraw, CVColor, DrawParameters, DrawPed, DrawVehicle
from ui import ParaList
from math import isnan

class FlowPlayer(object):
    @classmethod
    def draw(cls, mess, img):
        
        if 'vehicle_warning' in mess:
            data = mess['vehicle_warning']
            vid, headway, fcw, hw, vb = '-','-','-','-','-'

            vid = data['vehicle_id']
            headway = '%.2f' % data['headway']
            fcw = data['fcw']
            hw = data['headway_warning']
            vb = data['vb_warning']
            title = 'vehicle'
            para_list = [
                'vid:' + str(vid),
                'headway:' + str(headway),
                'fcw:' + str(fcw),
                'hw:' + str(hw),
                'vb:' + str(vb)
            ]
            BaseDraw.draw_single_info(img, (5, 0), 120, title, para_list)
            # DrawParameters.draw_normal_parameters(img, para_list, (100, 0))

        if 'vehicle_trace_res_list' in mess and None:
            res_list = mess['vehicle_trace_res_list']
            for rect in res_list:
                DrawPed.draw_ped_rect(img, rect['det_rect'])

        if 'vehicle_measure_res_list' in mess:
            res_list = mess['vehicle_measure_res_list']
            for i, vehicle in enumerate(res_list):
                pos= vehicle['det_rect']
                color = CVColor.Red if vehicle['is_crucial'] else CVColor.Cyan
                DrawVehicle.draw_vehicle_rect(img, pos, color, 2)
                
                '''
                cls.draw_vehicle_info(img, pos,
                                      vehicle['longitude_dist'],
                                      vehicle['lateral_dist'],
                                      0, str(vehicle['vehicle_class']))
                '''

                d1 = vehicle['longitude_dist']
                d2 = vehicle['lateral_dist']
                d1 = 'nan' if isnan(d1) else int(float(d1) * 100) / 100
                d2 = 'nan' if isnan(d2) else int(float(d2) * 100) / 100
                para_list = [
                    'v:'+str(d1)+' h:'+str(d2),
                    'type:'+str(vehicle['vehicle_class']),
                    'type:'+str(vehicle['vehicle_class'])
                ]
                '''
                rect = (int(pos[0]), int(pos[1])-46, 120, 46)
                BaseDraw.draw_alpha_rect(img, rect, 0.4)
                BaseDraw.draw_para_list(img, pos[0:2], para_list, -1, 20, 0.6)
                '''
                BaseDraw.draw_head_info(img, pos[0:2], para_list, 120)

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
