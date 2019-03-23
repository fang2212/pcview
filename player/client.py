import os
import cv2
import datetime
import numpy as np
from .ui import BaseDraw, CVColor, DrawParameters, DrawPed, DrawVehicle
from math import isnan

class ClientPlayer(object):
    def __init__(self, cfg):
        self.cfg = cfg

    def draw(self, mess):
        img = mess['img']
        frame_id = mess['frame_id']
        vehicle_data = mess['vehicle']
        lane_data = mess['lane']
        ped_data = mess['ped']
        tsr_data = mess['tsr']
        extra = mess['extra']

        self.draw_vehicle(img, vehicle_data, self.cfg.get('vehicle'))

        self.draw_lane(img, lane_data, self.cfg.get('lane'))

        self.draw_ped(img, ped_data, self.cfg.get('ped'))

        self.draw_tsr(img, tsr_data, self.cfg.get('tsr'))

        self.draw_env(img, frame_id, vehicle_data, lane_data, self.cfg.get('env'))

        return img
    
    @classmethod
    def draw_env(self, img, frame_id, vehicle_data, lane_data, cfg):
        light_mode = '-'
        if vehicle_data:
            light_mode = vehicle_data['light_mode']
        speed = vehicle_data.get('speed')*3.6 if vehicle_data.get('speed') else 0
        if not speed:
            speed = lane_data.get('speed') if lane_data.get('speed') else speed
        speed = "%.1f" % speed
        fps = 20
        t1 = datetime.datetime.now().strftime('%Y-%m-%d')
        t2 = datetime.datetime.now().strftime('%H:%M:%S')
        if cfg.get('show'):
            para_list = [
                'speed:' + str(speed),
                'light:' + str(light_mode),
                'fps:' + str(fps),
                'fid:' + str(frame_id),
                '' + str(t1),
                '' + str(t2)
            ]
            BaseDraw.draw_single_info(img, (5, 0), 120, 'env', para_list)

    @classmethod
    def draw_vehicle(cls, img, data, cfg):
        ttc, fcw, hwm, hw, vb = '-', '-', '-', '-', '-'
        if data:
            focus_index = data['focus_index']
            for i, obj in enumerate(data['dets']):
                pos = obj['bounding_rect']
                pos = pos['x'], pos['y'], pos['width'], pos['height']
                color = CVColor.Red if focus_index == i else CVColor.Cyan
                if cfg.get('show_obj'):
                    BaseDraw.draw_obj_rect(img, pos, color, cfg.get('thickness'))
                if cfg.get('show_info'):
                    d1 = obj['vertical_dist']
                    d2 = obj['horizontal_dist']
                    d1 = int(float(d1) * 100) / 100
                    d2 = int(float(d2) * 100) / 100
                    para_list = [
                        'v:'+str(d1),
                        'h:'+str(d2),
                    ]
                    BaseDraw.draw_head_info(img, pos[0:2], para_list, 80)
                if focus_index == i:
                    ttc = '%.2f' % obj['rel_ttc']
                    fcw = data['forward_collision_warning']
                    hw = data['headway_warning']
                    hwm = '%.2f' % data['ttc']
                    vb = data['bumper_warning']
                    if ttc == '1000.00':
                        ttc = '-'
        if cfg.get('show_warning'):
            para_list = [
                'headway:' + str(hwm),
                'ttc:' + str(ttc),
                'fcw:' + str(fcw),
                'hw:' + str(hw),
                'vb:' + str(vb)
            ]
            BaseDraw.draw_single_info(img, (125, 0), 120, 'vehicle', para_list)

    @classmethod
    def draw_lane(cls, img, data, cfg):
        lw_dis, rw_dis = '-', '-'
        if data:
            speed = data['speed']
            deviate_state = data['deviate_state']
            if cfg.get('show_obj'):
                BaseDraw.draw_lane_lines(img, data['lanelines'], speed,
                                         deviate_state, False, cfg.get('speed_limit'))
            lw_dis = '%.2f' % (data['left_wheel_dist'])
            rw_dis = '%.2f' % (data['right_wheel_dist'])
            if lw_dis == '111.00':
                lw_dis = '-'
            if rw_dis == '111.00':
                rw_dis = '-'
        if cfg.get('show_warning'):
            para_list = [
                'lw_dis:' + str(lw_dis),
                'rw_dis:' + str(rw_dis)
            ]
            BaseDraw.draw_single_info(img, (245, 0), 120, 'lane', para_list)


    @classmethod
    def draw_ped(self, img, data, cfg):
        pcw_on = '-'
        if data:
            for pedestrain in data['pedestrians']:
                position = pedestrain['regressed_box']
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Yellow
                if pedestrain['is_key']:
                    color = CVColor.Pink
                if cfg.get('show_obj'):
                    BaseDraw.draw_obj_rect(img, position, color, cfg.get('thickness'))
        if cfg.get('show_warning'):
            if data.get('pcw_on'):
                pcw_on = 1
            para_list = [
                'pcw_on:' + str(pcw_on)
            ]
            BaseDraw.draw_single_info(img, (365, 0), 120, 'ped', para_list)
        

    @classmethod
    def draw_tsr(self, img, data, cfg):
        
        def draw_tsr_info(img, position, max_speed):
            x1, y1, width, height = list(map(int, position))
            x2 = x1 + width
            y2 = y1 + height
            origin_x = max(0, x2 - 40)
            origin_y = max(0, y2)
            BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 40, 20), 0.6)
            BaseDraw.draw_text(img, str(max_speed), (x2 - 30, y2 + 5),
                               1, CVColor.Green, 1)

        if data:
            for i, tsr in enumerate(data['dets']):
                position = tsr['position']
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Red
                if cfg.get('show_obj'):
                    BaseDraw.draw_obj_rect(img, position, color, cfg.get('thickness'))
                if cfg.get('show_inf') and tsr['max_speed'] != 0:
                    draw_tsr_info(img, position, tsr['max_speed'])
        if cfg.get('show_warning'):
            speed_limit = data.get('speed_limit')
            para_list = [
                'speed_limit:' + str(speed_limit)
            ]
            BaseDraw.draw_single_info(img, (485, 0), 120, 'tsr', para_list)