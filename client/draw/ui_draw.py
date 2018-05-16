#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua<pengquanhua.minieye.cc>'
__version__ = '0.1.0'
__name____ = 'ui_draw'

import cv2
import os
import numpy as np
from etc.define import logodir
from .base import BaseDraw
from .base import CVColor

pack = os.path.join

class Player(object):
    
    def __init__(self):
        self.overlook_background_image = cv2.imread(pack(logodir, 'back.png'))
        self.circlesmall_image = cv2.imread(pack(logodir, 'circlesmall.tif'))
        self.sectorwide_image = cv2.imread(pack(logodir, 'sectorwide.tif'))
        self.sectorthin_image = cv2.imread(pack(logodir, 'sectorthin.tif'))
        self.car_image = cv2.imread(pack(logodir, 'car.tif'))
        self.overlook_othercar_image = cv2.imread(pack(logodir, 'othercar.tif'))
        self.overlook_beforecar_image = cv2.imread(pack(logodir, 'before.tif'))

    def show_overlook_background(self, img):
        y_background, x_background, _ = self.overlook_background_image.shape
        y_img, x_img, _ = img.shape
        roi_img = img[0 : y_background, x_img - x_background : x_img]
        cv2.addWeighted(self.overlook_background_image, 1, roi_img, 0.8, 0.0, roi_img)

        x_center, y_center = 1144, 240

        data_r = int(1) % 20 + 120

        draw_r = []
        while data_r > 30:
            draw_r.append(data_r)
            data_r = data_r - 20
        draw_r.append(140)

        y_circle, x_circle, _ = self.circlesmall_image.shape
        for R in draw_r:
            x_new, y_new = int(R), int(y_circle * R / x_circle)
            new_circle = cv2.resize(self.circlesmall_image, (y_new, x_new),
                                    interpolation=cv2.INTER_CUBIC)
            x_begin = x_center - x_new // 2
            x_end = x_begin + x_new
            y_begin = y_center - y_new // 2
            y_end = y_begin + y_new
            roi_img = img[y_begin : y_end, x_begin : x_end]
            cv2.addWeighted(new_circle, 0.5, roi_img, 1.0, 0.0, roi_img)

        
        for sector_in in [self.sectorwide_image, self.sectorthin_image]:
            y_sector, x_sector, _ = sector_in.shape
            x_begin = 1145 - x_sector // 2
            x_end = x_begin + x_sector
            y_end = 219
            y_begin = y_end - y_sector
            roi_img = img[y_begin : y_end, x_begin : x_end]
            cv2.addWeighted(sector_in, 0.5, roi_img, 1.0, 0.0, roi_img)
        
        y_car, x_car, _ = self.car_image.shape
        x_begin = x_center - x_car // 2
        x_end = x_begin + x_car
        y_begin = y_center - y_car // 2
        y_end = y_begin + y_car
        roi_img = img[y_begin : y_end, x_begin : x_end]
        cv2.addWeighted(self.car_image, 1.0,
                              roi_img, 1.0, 0.0, roi_img)
    
    def show_parameters_background(self, img):

        BaseDraw.draw_alpha_rect(img, (0, 0, 350, 170), 0.4)
        BaseDraw.draw_text(img, 'env', (10, 20), 0.5, CVColor.Cyan, 1)
        BaseDraw.draw_text(img, 'vechicle', (110, 20), 0.5, CVColor.Cyan, 1)
        BaseDraw.draw_text(img, 'lane', (210, 20), 0.5, CVColor.Cyan, 1)
        
    def show_vehicle(self, img, position, color=CVColor.Cyan, thickness = 2):
        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        BaseDraw.draw_vehicle_rect_corn(img, (x1, y1), (x2, y2), color, thickness)
    
    def show_vehicle_info(self, img, position, vertical_dis, horizontal_dis, vehicle_width, vehicle_type):
        
        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        origin_x = max(0, x2 - 200)
        origin_y = max(0, y1 - 20)
        BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 200, 20), 0.6)
        const_type = {
            '2': 'CAR',
            '3': 'BUS',
            '4': 'BOX',
            '5': 'SSP'
        }
        BaseDraw.draw_text(img, const_type[vehicle_type], (x2 - 190, y1 - 5),
                          0.5, CVColor.White, 1)

        d1 = int(float(vertical_dis) * 100) / 100
        d2 = int(float(horizontal_dis) * 10) / 10
        data = str(d1) + ',' + str(d2)
        BaseDraw.draw_text(img, data, (x2 - 150, y1 - 5), 0.5, CVColor.White, 1)

        vehicle_width = '%.2f' % vehicle_width 
        BaseDraw.draw_text(img, str(vehicle_width), (x2 - 50, y1 - 5), 0.5, CVColor.White, 1)
    
    def show_overlook_vehicle(self, img, type, y, x):
        d_y = int(float(y))
        d_x = int(float(x))
        y_car = max(20, 190 - d_y * 2)
        typ = int(type)
        if typ == 0:
            car = self.overlook_othercar_image
        else:
            car = self.overlook_beforecar_image
        x_car = 1144 + int(10 * d_x)

        y_shape, x_shape, _ = car.shape
        x_begin = x_car - x_shape // 2
        x_end = x_begin + x_shape
        y_begin = y_car - y_shape // 2
        y_end = y_begin + y_shape

        roi_img = img[y_begin: y_end, x_begin: x_end]
        cv2.addWeighted(car, 0.5, roi_img, 1.0, 0.0, roi_img)
    
    def show_vehicle_parameters(self, img, parameters):
        type = parameters[0]
        index = parameters[1]
        ttc = parameters[2]
        fcw = parameters[3]
        hwm = parameters[4]
        hw = parameters[5]
        vb = parameters[6]

        origin_x = 110
        origin_y = 40
        gap_v = 20
        BaseDraw.draw_text(img, 'type:' + type, (origin_x, origin_y), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'index:' + index, (origin_x, origin_y + gap_v), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'ttc:' + ttc, (origin_x, origin_y + gap_v * 2), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'fcw:' + fcw, (origin_x, origin_y + gap_v * 3), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'hwm:' + hwm, (origin_x, origin_y + gap_v * 4), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'hw:' + hw, (origin_x, origin_y + gap_v * 5), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'vb:' + vb, (origin_x, origin_y + gap_v * 6), 0.5, CVColor.White, 1)
    
    def show_lane(self, img, ratios, width, color):
        a0, a1, a2, a3 = ratios
        a0 = float(a0)
        a1 = float(a1)
        a2 = float(a2)
        a3 = float(a3)
        
        width = int(float(width) * 10 + 0.5)

        for y in range(450, 720, 50):
            y1 = y
            y2 = y1 + 50
            x1 = (int)(a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1)
            x2 = (int)(a0 + a1 * y2 + a2 * y2 * y2 + a3 * y2 * y2 * y2)            
            BaseDraw.draw_line(img, (x1, y1), (x2, y2), CVColor.Cyan, width)
    
    def show_lane_info(self, img, ratios, index, width, type, conf, color):
        a0, a1, a2, a3 = ratios
        a0 = float(a0)
        a1 = float(a1)
        a2 = float(a2)
        a3 = float(a3)
        
        color = CVColor.Cyan
        y1 = 450
        x1 = (int)(a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1)
        BaseDraw.draw_text(img, 'index:' + str(index), (x1, y1-45), 0.5, color, 1)
        width = '%.2f' % width
        BaseDraw.draw_text(img, 'width:' + str(width), (x1, y1-30), 0.5, color, 1)
        BaseDraw.draw_text(img, 'type:' + str(type), (x1, y1-15), 0.5, color, 1)
        BaseDraw.draw_text(img, 'conf:' + str(conf), (x1, y1), 0.5, color, 1)
    
    def show_overlook_lane(self, img, ratios, color):
        a0, a1, a2, a3 = ratios
        a0 = float(a0)
        a1 = float(a1)
        a2 = float(a2)
        a3 = float(a3)

        for y in range(0, 60, 2):
            y1 = y
            y2 = y1 + 2
            x1 = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            x2 = a0 + a1 * y2 + a2 * y2 * y2 + a3 * y2 * y2 * y2
            x1 = 1144 + int(x1 * 10)
            x2 = 1144 + int(x2 * 10)
            y1 = 240 - y1 * 2
            y2 = 240 - y2 * 2
            BaseDraw.draw_line(img, (x1, y1), (x2, y2), CVColor.Cyan, 1)

    def show_lane_parameters(self, img, parameters):
        lw_dis = parameters[0]
        rw_dis = parameters[1]
        ldw = parameters[2]
        trend = parameters[3]

        origin_x = 210
        origin_y = 40
        gap_v = 20
        BaseDraw.draw_text(img, 'lw_dis:'+lw_dis, (origin_x, origin_y), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'rw_dis:'+rw_dis, (origin_x, origin_y+gap_v), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'ldw:'+ldw, (origin_x, origin_y+gap_v*2), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'trend:'+trend, (origin_x, origin_y+gap_v*3), 0.5, CVColor.White, 1)
        
    def show_env(self,img, speed, light_mode, fps):
        BaseDraw.draw_text(img, 'light:'+ str(light_mode), (10, 40), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'speed:'+ str(int(speed)), (10, 60), 0.5, CVColor.White, 1)
        BaseDraw.draw_text(img, 'fps:'+ str(int(fps)), (10, 80), 0.5, CVColor.White, 1)