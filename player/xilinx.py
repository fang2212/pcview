import os
import cv2
import datetime
import numpy as np
from .ui import BaseDraw, CVColor, DrawParameters, DrawPed, DrawVehicle, \
                VehicleType
from math import isnan


class Avg(object):
    def __init__(self, len=10):
        self._l = []
        self.len = len
        self.avg = 0

    def append(self, val):
        self._l.append(val)
        if len(self._l) > self.len:
            self._l.pop(0)
        sum = 0
        for val in self._l:
            sum += val
        
        self.avg = sum/(len(self._l))
        return self.avg
    
    def get_avg(self):
        return self.avg
        

class FlowPlayer(object):
    def __init__(self, cfg={}):
        self.cfg = cfg
        self.sys_cpu_avg = Avg(10)
        self.rotor_cpu_avg = Avg(10)

    def draw(self, mess, img):
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
                'speed:' + str(speed)+'km/h',
                '' + str(t1),
                '' + str(t2)
            ]
            BaseDraw.draw_single_info(img, (0, 0), 140, title, para_list)
        # speed = float(mess['speed'])
        deviate_state = -1

        '''
        if 'system' in mess:
            self.draw_sys(img, mess.get('system'), self.cfg.get('system'))
        '''

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
                # BaseDraw.draw_obj_rect(img, obj['detect_box'], CVColor.Cyan, 1)
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
                    data[key] = "%.2f" % float(data[key])
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

        '''
        if 'vehicle_hit_list' in mess:
            res_list = mess['vehicle_hit_list']
            for i, obj in enumerate(res_list):
                BaseDraw.draw_obj_rect(img, obj['det_rect'], CVColor.Red, 1)

        if 'ped_hit_list' in mess:
            res_list = mess['ped_hit_list']
            for i, obj in enumerate(res_list):
                BaseDraw.draw_obj_rect(img, obj['det_rect'], CVColor.Green, 1)
        '''

        if 'vehicle_measure_res_list' in mess:
            res_list = mess['vehicle_measure_res_list']
            for i, vehicle in enumerate(res_list):
                # BaseDraw.draw_obj_rect(img, vehicle['det_rect'], CVColor.Cyan, 1)
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
            BaseDraw.draw_lane_lines(img, data, 222, deviate_state, draw_all=True, speed_limit=0)
        return img

    def draw_sys(self, img, data, cfg=None):
        sys_cpu = '-'
        rotor_cpu = '-'
        sys_mem = '-'
        rotor_mem = '-'
        load_avg1 = '-'
        load_avg5 = '-'
        load_avg15 = '-'
        loop_id = '-'
        if data:
            sys_cpu = data.get('system_cpu_utilization')
            rotor_cpu = data.get('rotor_cpu_utilization')
            sys_cpu = '%.2f' % self.sys_cpu_avg.append(sys_cpu)
            rotor_cpu = '%.2f' % self.rotor_cpu_avg.append(rotor_cpu)

            loop_id = str(data.get('loop_id'))
            sys_mem = '%.2f' % data.get('system_mem_utilization')
            rotor_mem = '%.2f' % data.get('rotor_mem_utilization')
            load_avg1 = '%.2f' % data.get('load_average_1')
            load_avg5 = '%.2f' % data.get('load_average_5')
            load_avg15 = '%.2f' % data.get('load_average_15')
        para_list = [
            'sys_cpu:'+sys_cpu,
            'rotor_cpu:'+rotor_cpu,
            'sys_mem:'+sys_mem,
            'rotor_mem:'+rotor_mem,
            'load_avg1:'+load_avg1,
            'load_avg5:'+load_avg5,
            'load_avg15:'+load_avg15,
            'loop_id:'+loop_id
        ]
        BaseDraw.draw_single_info(img, (1120, 0), 160, 'system', para_list)