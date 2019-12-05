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
            speed = 3.6*float(mess['speed'])
            speed_limit = self.cfg.get('lane_speed_limit', 0)
            lane_begin = self.cfg.get('lane_begin', 0)
            for lane in mess['lane']:
                if ((int(lane['label']) in [1, 2])) and speed >= speed_limit:
                    index = lane['label']
                    begin = lane_begin or int(lane['end'][1])
                    end = int(lane['start'][1])
                    begin = max(begin, 0)
                    end = min(end, 720)
                    
                    color = CVColor.Blue
                    #if 'warning' in lane:
                    #    if lane['warning'] and int(index) == int(deviate_state):
                    #        color = CVColor.Red
                    if self.cfg.get('lane_pts'):
                        BaseDraw.draw_polylines(img, lane['perspective_view_pts'], color, 2)
                    else:
                        BaseDraw.draw_lane_line(img, lane['perspective_view_poly_coeff'],
                                        0.2, color, begin, end)
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


pack = os.path.join
logodir = "assets/overlook"
class DrawOverlook(object):
    '''
    画右上角的俯视图
    '''
    overlook_background_image = cv2.imread(pack(logodir, 'back.png'))
    circlesmall_image = cv2.imread(pack(logodir, 'circlesmall.tif'))
    sectorwide_image = cv2.imread(pack(logodir, 'sectorwide.tif'))
    sectorthin_image = cv2.imread(pack(logodir, 'sectorthin.tif'))
    car_image = cv2.imread(pack(logodir, 'car.tif'))
    overlook_othercar_image = cv2.imread(pack(logodir, 'othercar.tif'))
    overlook_beforecar_image = cv2.imread(pack(logodir, 'before.tif'))

    def __init__(self, img):
        """绘制俯视图的背景，包括背景图，车背景图，光线图
        :param img: 原始图片
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

    def draw_vehicle(self, img, type, y, x):
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
        print(y_begin, x_end)

        roi_img = img[y_begin: y_end, x_begin: x_end]
        cv2.addWeighted(car, 0.5, roi_img, 1.0, 0.0, roi_img)

    def draw_lane(self, img, ratios, color):
        """在俯视图绘制车道线
        Args:
            img: 原始数据
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            color: CVColor 车道线颜色
        """
        a0, a1, a2, a3 = list(map(float, ratios))
        for y in range(0, 60, 2):
            y1 = y
            y2 = y1 + 2
            x1 = a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1
            x2 = a0 + a1 * y2 + a2 * y2 * y2 + a3 * y2 * y2 * y2
            x1 = 1144 + int(x1 * 10)
            x2 = 1144 + int(x2 * 10)
            y1 = 240 - y1 * 2
            y2 = 240 - y2 * 2
            BaseDraw.draw_line(img, (x1, y1), (x2, y2), color, 1)

    @classmethod
    def draw_lane_pts(self, img, pts, color):
        nps = []
        for ts in pts:
            x, y = list(map(int, pt))
            x = 1144 + x*10
            y = 240 - y*2
            nps.append( (x,y) )
        for i in range(1, len(nps)):
            BaseDraw.draw_line(img, nps[i-1], nps[i], color, 1)