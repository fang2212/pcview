import os
import cv2
import datetime
import numpy as np
from .ui import BaseDraw, CVColor, DrawParameters, DrawPed, DrawVehicle
from math import isnan

class ClientPlayer(object):
    @classmethod
    def draw(cls, mess):
        img = mess['img']
        frame_id = mess['frame_id']
        vehicle_data = mess['vehicle']
        lane_data = mess['lane']
        ped_data = mess['ped']
        tsr_data = mess['tsr']
        extra = mess['extra']

        cls.draw_vehicle(img, vehicle_data)

        cls.draw_lane(img, lane_data)

        cls.draw_ped(img, ped_data)

        cls.draw_tsr(img, tsr_data)

        return img
    
    @classmethod
    def draw_vehicle(cls, img, data):
        if not data:
            return
        focus_index = data['focus_index']
        for i, vehicle in enumerate(data['dets']):
            position = vehicle['bounding_rect']
            position = position['x'], position['y'], position['width'], position['height']
            color = CVColor.Red if focus_index == i else CVColor.Cyan
            BaseDraw.draw_obj_rect_corn(img, position, color, 1, 8)

    @classmethod
    def draw_lane(cls, img, data):
        if not data:
            return
        speed = data['speed']
        deviate_state = data['deviate_state']
        BaseDraw.draw_lane_lines(img, data['lanelines'], speed, deviate_state, False, 0)

    @classmethod
    def draw_ped(cls, img, data):
        if not data:
            return
        for pedestrain in data['pedestrians']:
            position = pedestrain['regressed_box']
            position = position['x'], position['y'], position['width'], position['height']
            color = CVColor.Yellow
            if pedestrain['is_key']:
                color = CVColor.Pink
            #if pedestrain['is_danger']:
            #    color = CVColor.Pink
            BaseDraw.draw_obj_rect(img, position, color, 1)

    @classmethod
    def draw_tsr(cls, img, data):
        if not data:
            return
        
        def draw_tsr_info(img, position, max_speed):
            x1, y1, width, height = list(map(int, position))
            x2 = x1 + width
            y2 = y1 + height
            origin_x = max(0, x2 - 40)
            origin_y = max(0, y2)
            BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 40, 20), 0.6)
            BaseDraw.draw_text(img, str(max_speed), (x2 - 30, y2 + 5),
                               1, CVColor.Green, 1)
        for i, tsr in enumerate(data['dets']):
            position = tsr['position']
            position = position['x'], position['y'], position['width'], position['height']
            color = CVColor.Red
            BaseDraw.draw_obj_rect(img, position, color, 1)
            if tsr['max_speed'] != 0:
                draw_tsr_info(img, position, tsr['max_speed'])                