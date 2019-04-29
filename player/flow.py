import os
import cv2
import datetime
import numpy as np
from .ui import BaseDraw, CVColor, VehicleType
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
                'fps:' + str(fps),
                'speed:' + str(speed)+'km/h',
                'fid:' + str(mess.get('frame_id')),
                '' + str(t1),
                '' + str(t2)
            ]
            BaseDraw.draw_single_info(img, (0, 0), 140, title, para_list)
        # speed = float(mess['speed'])
        deviate_state = -1

        title = 'system'
        para_list = []
        if 'system' in mess:
            para_list += self.sys_info(img, mess.get('system'), self.cfg.get('system'))
        if 'camera' in mess:
            s_ts = mess['camera']['create_ts']
            if 'finish_time_us' in mess:
                
                # print(mess['finish_time_us'])
                f_ts = mess['finish_time_us']['time_us']

                delay = "%.1f" % ((f_ts-s_ts)/1000)
                para_list += [
                    'total_delay:' + str(delay)
                ]
                # print(para_list)
            else:
                total_ts = -1
                lane_ts = mess.get('lane_finish_time')
                vehicle_ts = mess.get('vehicle_finish_time')
                tsr_ts = mess.get('tsr_finish_time')
                if lane_ts:
                    total_ts = max(total_ts, (lane_ts-s_ts)/1000)
                    para_list += [
                        'lane_delay:' + str("%.1f" % total_ts)
                    ]
                if vehicle_ts:
                    total_ts = max(total_ts, (vehicle_ts-s_ts)/1000)
                    para_list += [
                        'vehicle_delay:' + str("%.1f" % ((vehicle_ts-s_ts)/1000))
                    ]
                if tsr_ts:
                    total_ts = max(total_ts, (tsr_ts-s_ts)/1000)
                    para_list += [
                        'tsr_delay:' + str("%.1f" % ((tsr_ts-s_ts)/1000))
                    ]
                if total_ts > 0:
                    para_list += [
                        'total_delay:' + str(total_ts)
                    ]
        # print('para', para_list)
        BaseDraw.draw_single_info(img, (1120, 0), 160, 'system', para_list)
        print(' '.join(para_list))

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
                BaseDraw.draw_obj_rect(img, obj['detect_box'], CVColor.Cyan, 1)
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
            ld = '--' if float(data["left_wheel_dist"])>= 111 else data["left_wheel_dist"]
            rd = '--' if float(data["right_wheel_dist"])>= 111 else data["right_wheel_dist"]
            para_list = [
                "latest_dist:"+data["latest_dist"],
                "lateral_speed:"+data["lateral_speed"],
                "earliest_dist:"+data["earliest_dist"],
                "deviate_state:"+data["deviate_state"],
                "deviate_trend:"+data["deviate_trend"],
                "lt_wheel_dist:"+ld,
                "rt_wheel_dist:"+rd,
                "warning_dist:"+data["warning_dist"]
            ]
            BaseDraw.draw_single_info(img, (390, 0), 180, 'lane', para_list)
            #BaseDraw.draw_lane_warnning(img, (750, 60), deviate_state)

        if 'vehicle_warning' in mess:
            data = mess['vehicle_warning']
            vid, headway, fcw, hw, vb, ttc = '-', '-', '-', '-', '-', '-'

            vid = data['vehicle_id']
            vid = '-' if int(vid) == -1 else vid
            headway =  '--' if float(data['headway']) >= 999 else '%.2f' % data['headway']
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

        if 'vehicle_hit_list' in mess:
            res_list = mess['vehicle_hit_list']
            for i, obj in enumerate(res_list):
                BaseDraw.draw_obj_rect(img, obj['det_rect'], CVColor.Red, 1)

        if 'ped_hit_list' in mess:
            res_list = mess['ped_hit_list']
            for i, obj in enumerate(res_list):
                BaseDraw.draw_obj_rect(img, obj['det_rect'], CVColor.Green, 1)

        if 'tsr_trace_res_list' in mess:
            res_list = mess['tsr_trace_res_list']
            for i, obj in enumerate(res_list):
                BaseDraw.draw_obj_rect(img, obj['reg_rect'], CVColor.Red, 1)
                pos = obj['reg_rect']
                tsr_class = obj['tsr_class']
                tsr_id = obj['tsr_id']
                track_cnt = obj['track_cnt']
                para_list = [
                    'class:'+str(tsr_class),
                    'id:'+str(tsr_id),
                    'track_cnt:'+str(track_cnt)
                ]
                BaseDraw.draw_head_info(img, pos[0:2], para_list, 100)

        if 'tsr_warning' in mess:
            data = mess['tsr_warning']
            height_limit = '%.2f' % data['height_limit']
            weight_limit = '%.2f' % data['weight_limit']
            speed_limit = data['speed_limit']
            tsr_warning_level = data['tsr_warning_level']
            title = 'tsr'
            para_list = [
                'height_limit:'+str(height_limit),
                'weight_limit:'+str(weight_limit),
                'speed_limit:'+str(speed_limit),
                #'warning_level:'+str(tsr_warning_level)
            ]
            BaseDraw.draw_single_info(img, (570, 0), 150, title, para_list)

        if 'vehicle_measure_res_list' in mess:
            res_list = mess['vehicle_measure_res_list']
            for i, vehicle in enumerate(res_list):
                BaseDraw.draw_obj_rect(img, vehicle['det_rect'], CVColor.Cyan, 1)
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

        if 'can' in mess:
            DrawAlarmCan.draw(img, mess['can'])

        if 'lane' in mess:
            speed = 3.6*float(mess['speed'])
            speed_limit = self.cfg.get('lane_speed_limit', 0)
            print('speed:', speed, speed_limit)
            lane_begin = self.cfg.get('lane_begin', 0)
            for lane in mess['lane']:
                if ((int(lane['label']) in [1, 2])) and speed >= speed_limit:
                    index = lane['label']
                    begin = lane_begin or int(lane['end'][1])
                    end = int(lane['start'][1])
                    begin = max(begin, 0)
                    end = min(end, 720)
                    
                    color = CVColor.Blue
                    if 'warning' in lane:
                        if lane['warning'] and int(index) == int(deviate_state):
                            color = CVColor.Red

                    if self.cfg.get('lane_pts'):
                        BaseDraw.draw_polylines(img, lane['perspective_view_pts'], color, 2)
                    else:
                        BaseDraw.draw_lane_line(img, lane['perspective_view_poly_coeff'],
                                        0.2, color, begin, end)
        return img

    def sys_info(self, img, data, cfg=None):
        para_list = []
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
        return para_list

def chr(d):
    return str(d)[0]

class DrawAlarmCan(object):
    '''
    突出显示报警提示, can数据
    '''
    @classmethod
    def draw(self, img, info):
        #info = mess['info']
        info1 = {
            "hw_on": 1,
            "ldw_on": 1,
            "lld": 1,
            "rld": 1,
        }
        fcw, = dict2list(info, ['fcw', ], int, -1)
        ped_on, pcw_on = dict2list(info, ['ped_on', 'pcw_on'], int, -1)
        hw_on, hw = dict2list(info, ['hw_on', 'hw'], int, -1)
        ttc, = dict2list(info, ['ttc'], float, -1)
        ldw_on, lld, rld, lldw, rldw = dict2list(info, ['ldw_on', 'lld', 'rld', 'lldw', 'rldw'], int, -1)
        tsr, = dict2list(info, ['overspeed'], int, -1)
        buzzing, = dict2list(info, ['buzzing'], str, '')
        camera, = dict2list(info, ['camera',], int, -1)

        ttc = "%2.1f"%ttc #if hw > 0 else "--"
        lldw = 2 if lld==0 else lldw
        rldw = 2 if rld==0 else rldw

        basex, basey, width, height = (730, 0, 250, 150)
        size, thickness = (0.6, 1)
        alarms = [
            ["CAM:"+chr(camera), 1, (0,18), int(camera>0), size, thickness],
            ["FCW:"+chr(fcw), 1, (0, 18), int(fcw>0), size, thickness],
            ["HWM:"+chr(hw)+"  ttc:"+ttc+"  on:"+chr(hw_on), 1, (0, 18), int(hw>1), size, thickness],
            ["PCW:"+chr(pcw_on)+"  ped:"+chr(ped_on), 1, (0, 18), int(pcw_on>0), size, thickness],
            ["TSR: "+chr(tsr), 1, (0, 18), int(tsr>0), size, thickness],
            ["AW :"+buzzing, 1, (0, 18), int(bool(buzzing)), size, thickness],
            ["|", 1, (0, 30), lldw, 1, 2],
            ["|", 1, (50, 0), rldw, 1, 2],
            ["on:"+chr(ldw_on), 1, (50, 0), int(ldw_on>0), size, thickness],
        ]
        
        color = [CVColor.Green, CVColor.Red, CVColor.White] # 不报警 报警 
        BaseDraw.draw_alpha_rect(img, (basex-10, basey, width, height), 0.4)
        x, y = (basex, basey)
        for alarm in alarms:
            text, show, pos, value, size, thickness = alarm
            if show:
                x += pos[0]
                y += pos[1]
                BaseDraw.draw_text(img, text, (x, y), size, color[value], thickness)

        BaseDraw.draw_text(img, "(can)", (basex, y+25), 0.4, CVColor.Yellow, 1)

def dict2list(d, keys, type=None, default=None):
    values = []
    for key in keys:
        value = d.get(key, default)
        if type:
            value = type(value)
        values.append(value)
    return values
