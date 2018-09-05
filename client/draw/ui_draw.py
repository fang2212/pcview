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
    """图片播放器"""

    def __init__(self):
        self.overlook_background_image = cv2.imread(pack(logodir, 'back.png'))
        self.circlesmall_image = cv2.imread(pack(logodir, 'circlesmall.tif'))
        self.sectorwide_image = cv2.imread(pack(logodir, 'sectorwide.tif'))
        self.sectorthin_image = cv2.imread(pack(logodir, 'sectorthin.tif'))
        self.car_image = cv2.imread(pack(logodir, 'car.tif'))
        self.overlook_othercar_image = cv2.imread(pack(logodir, 'othercar.tif'))
        self.overlook_beforecar_image = cv2.imread(pack(logodir, 'before.tif'))

    def show_overlook_background(self, img):
        """绘制俯视图的背景，包括背景图，车背景图，光线图

        Args:
            img: 原始图片
        """
        y_background, x_background, _ = self.overlook_background_image.shape
        y_img, x_img, _ = img.shape
        roi_img = img[0 : y_background, x_img - x_background : x_img]
        cv2.addWeighted(self.overlook_background_image, 1, roi_img, 0.4, 0.0, roi_img)

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
        x_begin = x_center - x_car // 2 -3
        x_end = x_begin + x_car
        y_begin = y_center - y_car // 2
        y_end = y_begin + y_car
        roi_img = img[y_begin : y_end, x_begin : x_end]
        cv2.addWeighted(self.car_image, 1.0,
                              roi_img, 1.0, 0.0, roi_img)
    
    def show_parameters_background(self, img, rect):
        """左上角参数背景图"""
        BaseDraw.draw_alpha_rect(img, rect, 0.4)
        
    def show_vehicle(self, img, position, color=CVColor.Cyan, thickness = 2):
        """绘制车辆框
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            color: CVColor 车辆颜色
            thickness: int 线粗
        """

        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        BaseDraw.draw_vehicle_rect_corn(img, (x1, y1), (x2, y2), color, thickness)
    
    def show_vehicle_info(self, img, position, vertical_dis, horizontal_dis, vehicle_width, vehicle_type):
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
        const_type = {
            '2': 'CAR',
            '3': 'BUS',
            '4': 'BOX',
            '5': 'SSP'
        }
        BaseDraw.draw_text(img, const_type[vehicle_type], (x2 - 150, y1 - 5),
                          size, CVColor.White, 1)

        d1 = int(float(vertical_dis) * 100) / 100
        d2 = int(float(horizontal_dis) * 10) / 10
        #data = str(d1) + ',' + str(d2)
        data = str(d1)
        BaseDraw.draw_text(img, data, (x2 - 90, y1 - 5), size, CVColor.White, 1)

        # vehicle_width = '%.2f' % vehicle_width 
        # BaseDraw.draw_text(img, str(vehicle_width), (x2 - 50, y1 - 5), 0.5, CVColor.White, 1)
 
    def show_overlook_vehicle(self, img, type, y, x):
        """在俯视图绘制车辆
        Args:
            img: 原始图片
            type: 是否关键车
            y: float 与检测车辆的竖直距离
            x: float 与检测车辆的水平距离
        """

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
    
    def show_lane(self, img, ratios, width, color):
        """绘制车道线
        Args:
            img: 原始图片
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            width: float 车道线宽度
            color: CVColor 车道线颜色
        """

        a0, a1, a2, a3 = ratios
        a0 = float(a0)
        a1 = float(a1)
        a2 = float(a2)
        a3 = float(a3)
        
        width = int(float(width) * 10 + 0.5)

        for y in range(480, 720, 20):
            y1 = y
            y2 = y1 + 20
            x1 = (int)(a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1)
            x2 = (int)(a0 + a1 * y2 + a2 * y2 * y2 + a3 * y2 * y2 * y2)            
            BaseDraw.draw_line(img, (x1, y1), (x2, y2), color, width)
    
    def show_lane_info(self, img, ratios, index, width, type, conf, color):
        """绘制车道线信息
        Args:
            img: 原始数据
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            index: 车道索引
            width: float 车道线宽度
            type: 车道线类型
            conf: 置信度
            color: CVColor 车道线颜色
        """
        a0, a1, a2, a3 = ratios
        a0 = float(a0)
        a1 = float(a1)
        a2 = float(a2)
        a3 = float(a3)
        
        color = CVColor.Cyan
        size = 1
        y1 = 500
        x1 = (int)(a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1)
        # BaseDraw.draw_text(img, 'index:' + str(index), (x1, y1-45), 0.5, color, 1)
        width = '%.2f' % width
        # BaseDraw.draw_text(img, 'width:' + str(width), (x1, y1-20), size, color, 1)
        BaseDraw.draw_text(img, 'width:' + str(width), (x1, y1), size, color, 1)
        # BaseDraw.draw_text(img, 'type:' + str(type), (x1, y1), size, color, 1)
        # BaseDraw.draw_text(img, 'conf:' + str(conf), (x1, y1), 0.5, color, 1)
    
    def show_overlook_lane(self, img, ratios, color):
        """在俯视图绘制车道线
        Args:
            img: 原始数据
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            color: CVColor 车道线颜色
        """
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

    def show_peds(self, img, position, color=CVColor.Cyan, thickness = 2):
        """绘制pedestrain
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            color: CVColor 颜色
            thickness: int 线粗
        """

        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        BaseDraw.draw_rect(img, (x1, y1), (x2, y2), color, thickness)
    
    def show_peds_info(self, img, position, distance):
        """绘制车辆信息
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            max_speed: float 
        """
        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        origin_x = max(0, x2 - 65)
        origin_y = max(0, y1 - 30)
        font_size = 1
        BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 65, 30), 0.6)
        BaseDraw.draw_text(img, ('%.1f' % distance), (x2 - 65, y1 - 5),
                          font_size, CVColor.White, 1)
    
    def show_tsr(self, img, position, color=CVColor.Cyan, thickness = 2):
        """绘制tsr框
        Args:
            img: 原始图片
            position: (x, y, width, height),框的位置，大小
            color: CVColor 颜色
            thickness: int 线粗
        """

        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        BaseDraw.draw_rect(img, (x1, y1), (x2, y2), color, thickness)
    
    def show_tsr_info(self, img, position, max_speed):
        """绘制车辆信息
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            max_speed: float 
        """
        x, y, width, height = position
        x1 = int(x)
        y1 = int(y)
        width = int(width)
        height = int(height)
        x2 = x1 + width
        y2 = y1 + height
        origin_x = max(0, x2 - 40)
        origin_y = max(0, y2)
        BaseDraw.draw_alpha_rect(img, (origin_x, origin_y, 40, 20), 0.6)
        BaseDraw.draw_text(img, str(max_speed), (x2 - 30, y2 + 5),
                          1, CVColor.Green, 1)
    
    def show_byd_can(self, img, can_data, lane_data):
        """显示can信息
        Args:
            img: 原始图片
            can_data: can信息 
        """
        print('recv can', can_data)
        color_dict = {
            0: CVColor.White,
            1: CVColor.Green,
            2: CVColor.Blue,
            3: CVColor.Red,
        }
        left_type = can_data.get('left_ldw')
        if not left_type in [0,1,2,3]:
            left_type = 0
        right_type = can_data.get('right_ldw')
        if not right_type in [0,1,2,3]:
            right_type = 0
        print(can_data)
        if lane_data.get('left_lamp'):
            left_lamp = 3
        else:
            left_lamp = 1
        if lane_data.get('right_lamp'):
            right_lamp = 3
        else:
            right_lamp = 1
        BaseDraw.draw_line(img, (600, 20), (600, 100), color_dict[left_type], 5)
        BaseDraw.draw_line(img, (680, 20), (680, 100), color_dict[right_type], 5)
        BaseDraw.draw_line(img, (600, 110), (600, 140), color_dict[left_lamp], 5)
        BaseDraw.draw_line(img, (680, 110), (680, 140), color_dict[right_lamp], 5)

    def show_normal_parameters(self, img, para_list, point):
        """显示ped信息
        Args:
            img: 原始图片
            parameters: List [index, TODO ]
        """
        origin_x, origin_y = point
        gap_v = 20
        size = 0.5
        BaseDraw.draw_text(img, para_list.type, (origin_x, origin_y + gap_v), size, CVColor.Cyan, 1)
        for index, para in enumerate(para_list.output()): 
            BaseDraw.draw_text(img, para, (origin_x, origin_y + gap_v * (index+2)), size, CVColor.White, 1)