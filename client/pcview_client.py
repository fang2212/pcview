#.!/usr/bin/python
# -*- coding:utf8 -*-

import time
import threading
import json
from datetime import datetime
from multiprocessing import Value
from .draw.base import BaseDraw
from .draw.base import CVColor
import os
import sys
                             
import cv2
from .draw.ui_draw import Player
from etc.config import config
from .FileHandler import FileHandler
from .Hub import MtkHub
from .Hub import FpgaHub

class PCViewer():
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, hub):
        self.hub = hub
        self.player = Player()
        self.exit = False

        if config.mobile.show:
            mobile_fp = open(config.mobile.path, 'r+')
            self.mobile_content = json.load(mobile_fp)
            mobile_fp.close()
        
        if config.save.log or config.save.alert or config.save.video:
            self.fileHandler = FileHandler()
            self.fileHandler.start()
    
    def start(self):
        self.hub.start()
        self.start_time = datetime.now()
        frame_cnt = 0

        while not self.exit:
            d = self.hub.pop()
            if not d.get('frame_id'):
                continue
            frame_cnt += 1
            self.draw(d, frame_cnt)
            if frame_cnt >= 500:
                self.start_time = datetime.now()
                frame_cnt = 0

    def draw(self, mess, frame_cnt):
        img = mess['img']
        frame_id = mess['frame_id']

        self.player.show_overlook_background(img)
        if config.mobile.show:
            bg_width = 120 * 5
        else:
            bg_width = 120 * 3
        self.player.show_parameters_background(img, (0, 0, bg_width, 170))
        
        if config.show.vehicle:
            self.draw_vehicle(img, mess['vehicle_data'])
        
        if config.show.lane:
            self.draw_lane(img, mess['lane_data'])

        if config.show.ped:
            self.draw_ped(img, mess['ped_data'])
        
        # show env info
        light_mode = -1
        if mess['vehicle_data']:
            lignt_mode = mess['vehicle_data']['light_mode']
        speed = mess['vehicle_data'].get('speed') if mess['vehicle_data'].get('speed') else 0
        speed = mess['lane_data'].get('speed')*3.6 if mess['lane_data'].get('speed') else speed

        fps = self.cal_fps(frame_cnt)
        self.player.show_env(img, speed, light_mode, fps, (0, 0))
        
        # save info
        if config.save.alert:
            alert = self.get_alert(mess['vehicle'], mess['lane_data'], mess['ped_data'])
            self.fileHandler.insert_alert((frame_id, {index: alert}))
            self.fileHandler.insert_image((index, img))

        if config.save.video:
            self.fileHandler.insert_video((frame_id, img))
        
        if config.save.log:
            temp_mess = mess
            temp_mess.pop('img')
            self.fileHandler.insert_log((frame_id, temp_mess))
        
        cv2.imshow('UI', img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            self.exit = True
        elif key == 27:
            cv2.destroyAllWindows()
            self.exit = True

    def get_alert(self, vehicle_data, lane_data, ped_data):
        alert = {}
        warning_level, alert_ttc, hw_state, fcw_state, vb_state, sg_state = 0,0,0,0,0,0
        if vehicle_data:
            speed = vehicle_data['speed']
            focus_index = vehicle_data['focus_index']
            if focus_index != -1:
                fcw_state = vehicle_data['forward_collision_warning']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                vb_state = vehicle_data['bumper_state']
                sg_state = vehicle_data['stop_and_go_state']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                warning_level = vehicle_data['warning_level']
                hw_state = vehicle_data['headway_warning']
        alert['ttc'] = float(alert_ttc)
        alert['warning_level'] = int(warning_level)
        alert['hw_state'] = int(hw_state)
        alert['fcw_state'] = int(fcw_state)
        alert['vb_state'] = int(vb_state)
        alert['sg_state'] = int(sg_state)

        lane_warning = 0
        if lane_data: 
            lane_warning = lane_data['deviate_state']
            speed = lane_data['speed']*3.6
        alert['lane_warning'] = lane_warning
        alert['speed'] = float('%.2f' % speed)
       
        return alert

    # vehicle
    def draw_vehicle(self, img, vehicle_data):
        v_type, index, ttc, fcw ,hwm, hw, vb = '-','-','-','-','-','-','-'
        if vehicle_data:
            focus_index = vehicle_data['focus_index']
            speed = vehicle_data['speed'] * 3.6
            for i, vehicle in enumerate(vehicle_data['dets']):
                focus_vehicle = (i == focus_index)
                position = vehicle['bounding_rect']
                
                color = CVColor.Red if focus_index == i else CVColor.Cyan
                self.player.show_vehicle(img, position, color, 2)
                
                self.player.show_vehicle_info(img, position,
                                        vehicle['vertical_dist'],vehicle['horizontal_dist'], 
                                        vehicle['vehicle_width'], str(vehicle['type']))
                self.player.show_overlook_vehicle(img, focus_vehicle,
                                            vehicle['vertical_dist'],
                                            vehicle['horizontal_dist'])
                
            if focus_index != -1:
                vehicle = vehicle_data['dets'][focus_index]
                v_type = vehicle['type']
                index = vehicle['index']
                ttc = '%.2f' % vehicle['rel_ttc']
                fcw = vehicle_data['forward_collision_warning']
                hw = vehicle_data['headway_warning']
                hwm = '%.2f' % vehicle_data['ttc']
                vb = vehicle_data['bumper_warning']
                if ttc == '1000.00':
                    ttc = '-'
        parameters = [str(v_type), str(index), str(ttc), str(fcw), str(hwm), str(hw), str(vb)]
        self.player.show_vehicle_parameters(img, parameters, (120, 0))
                    
    # lane
    def draw_lane(self, img, lane_data):
        lw_dis, rw_dis, ldw, trend = '-', '-', '-', '-'
        if lane_data:
            speed = lane_data['speed'] * 3.6
            for lane in lane_data['lanelines']:
                if int(lane['label']) in [1, 2] and speed >= config.show.lane_speed_limit:
                    color = CVColor.Cyan
                    width = lane['width']
                    l_type = lane['type']
                    conf = lane['confidence']
                    index = lane['label']
                    self.player.show_lane(img, lane['perspective_view_poly_coeff'], 
                                          0.2, color)
                    self.player.show_overlook_lane(img, lane['bird_view_poly_coeff'], color)
                    self.player.show_lane_info(img, lane['perspective_view_poly_coeff'],
                                               index, width, l_type, conf, color)

            lw_dis = '%.2f' % (lane_data['left_wheel_dist'])
            rw_dis = '%.2f' % (lane_data['right_wheel_dist'])
            ldw = lane_data['deviate_state']
            trend = lane_data['deviate_trend']
            if lw_dis == '111.00':
                lw_dis = '-'
            if rw_dis == '111.00':
                rw_dis = '-'
            
        parameters = [str(lw_dis), str(rw_dis), str(ldw), str(trend)]
        if config.mobile.show:
            lane_y = 120 * 3
        else:
            lane_y = 120 * 2
        self.player.show_lane_parameters(img, parameters, (lane_y, 0))

    # ped
    def draw_ped(self, img, ped_data):
        if ped_data:
            print('ped_data:', ped_data)
            for pedestrain in ped_data['pedestrians']:
                position = pedestrain['regressed_box']
                self.player.show_pedestrains(img, position, CVColor.Yellow, 2)
    
    def cal_fps(self, frame_cnt):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        duration = duration if duration > 0 else 1
        fps = frame_cnt / duration
        return fps

    def draw_mobile(self, img, frame_id):
        index = int(frame_id/3)*4+frame_id%3
        if config.mobile.show:
            mobile_ldw, mobile_hw, mobile_fcw, mobile_vb, mobile_hwm = '-', '-', '-', '-', '-'
            mobile_log = self.mobile_content[index]
            if mobile_log:
                mobile_hwm = mobile_log.get('headway_measurement') if mobile_log.get('headway_measurement') else 0
                mobile_hw = 1 if mobile_log.get('sound_type') == 3 else 0
                mobile_fcw = 1 if mobile_log.get('sound_type') == 6 and mobile_log.get('fcw_on') == 1 else 0
                mobile_vb = 1 if mobile_log.get('sound_type') == 5 else 0
                mobile_ldw = mobile_log['left_ldw'] * 2 + mobile_log['right_ldw'] if 'left_ldw' in mobile_log else 0

            mobile_parameters = [str(mobile_hwm), str(mobile_hw), str(mobile_fcw), str(mobile_vb), str(mobile_ldw)]
            self.player.show_mobile_parameters(img, mobile_parameters, (120*2, 0))

    def test(self):
        """用于测试，读取离线数据"""
        path = ""
        fp = open(os.path.join(path, 'log.json'), 'r')
        log_contents = fp.readlines()
        fp.close()
        
        frame_cnt = 0
        self.start_time = datetime.now()
        for data in log_contents:
            frame_cnt += 1
            if not self.exit:
                data = json.loads(data)
                img_path = os.path.join(path, str(data['frame_id']) + '.jpg')
                if not os.path.exists(img_path):
                    continue
                img = cv2.imread(img_path)
                data = {
                    'frame_id': data['frame_id'],
                    'img': img,
                    'lane_data': data['lane_data'],
                    'vehicle_data': data['vehicle_data']
                }
                self.draw(data, frame_cnt)
            else:
                break
