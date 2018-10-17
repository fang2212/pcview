
import os
import cv2
import numpy as np

from etc.config import config
from etc.define import logodir

pack = os.path.join

class CVColor(object):
    '''
    basic color RGB define
    '''
    Red = (0, 0, 255)
    Green = (0, 255, 0)
    Blue = (255, 0, 0)
    Cyan = (255, 255, 0)
    Magenta = (255, 0, 255)
    Yellow = (0, 255, 255)
    Black = (0, 0, 0)
    White = (255, 255, 255)
    Pink = (255, 0, 255)

class BaseDraw(object):
    """
    基本的opencv绘图函数
    """

    @classmethod
    def draw_text(cls, img_content, text, position, size, color, thickness, type=cv2.LINE_AA):
        """
        For anti-aliased text, add argument cv2.LINE_AA.
        sample drawText(img_content, text, (20, 30), 0.6, CVColor.Blue, 2)
        """
        cv2.putText(img_content, text, position,
                    cv2.FONT_HERSHEY_SIMPLEX, size, color,
                    thickness, type)
    
    @classmethod
    def draw_rect(cls, img_content, point1, point2, color, thickness=2):
        cv2.rectangle(img_content, point1, point2, color, thickness)

    @classmethod
    def draw_rect_corn(cls, img, point1, point2, color, thickness=2):
        """
            draw 8 lines at corns
        """
        x1, y1 = point1
        x2, y2 = point2
        width = abs(x2-x1)
        height = abs(y2-y1)
        suit_len = min(width, height)
        suit_len = int(suit_len / 6)
        
        # 左上角
        cv2.line(img, (x1,y1), (x1+suit_len, y1), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x1,y1), (x1, y1+suit_len), color, thickness, cv2.LINE_8, 0)

        # 右上角
        cv2.line(img, (x2-suit_len,y1), (x2, y1), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x2,y1), (x1+width, y1+suit_len), color, thickness, cv2.LINE_8, 0)

        # 左下角
        cv2.line(img, (x1,y2-suit_len), (x1, y2), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x1,y2), (x1+suit_len, y2), color, thickness, cv2.LINE_8, 0)

        # 右下角
        cv2.line(img, (x2-suit_len,y2), (x2, y2), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x2,y2-suit_len), (x2, y2), color, thickness, cv2.LINE_8, 0)


    @classmethod
    def draw_line(cls, img_content, p1, p2,  color_type = CVColor.White, thickness=1, type=cv2.LINE_8):
        cv2.line(img_content, p1, p2, color_type, thickness, type, 0)

    @classmethod
    def draw_lane_line(cls, img_content, line,  color_type='',
                       begin=420, end=650):
        """
        g = a0 + a1*x + a2*x*x + a3*x*x*x
        a0 = -28.0362
        a1 = 1.42638
        a2 = -2.64114e-05
        a3 = 0
        """
        a0 = float(line[0])
        a1 = float(line[1])
        a2 = float(line[2])
        a3 = float(line[3])

        for x in range(begin, end, 10):
            y = int(a0 + a1*x + a2*x*x + a3*x*x*x)
            x1 = x + 10
            y1 = int(a0 + a1*x1 + a2*x1*x1 + a3*x1*x1*x1)
            cv2.line(img_content, (y, x), (y1, x1), CVColor.White, 2,
                     cv2.LINE_AA, 0)

    @classmethod
    def draw_alpha_rect(cls, image_content, rect, alpha, color = CVColor.White, line_width = 0):
        x, y, w, h = rect
        img = np.zeros((h, w, 3), np.uint8)
        roi = image_content[y:y+h, x:x+w]
        cv2.addWeighted(img, 1.0, roi, alpha, 0.0, roi)
        if line_width > 0:
            cv2.rectangle(image_content, (x, y), (x+w, y+h), color, line_width)

    @classmethod
    def draw_polylines(cls, img, pts, color, thickness=2):
        pts = [pts]
        pts = np.array(pts)
        cv2.polylines(img, pts, False, color, thickness)

class ParaList(object):
    def __init__(self, para_type):
        self.type = para_type
        self.para_list = []
    def insert(self, para, value):
        self.para_list.append(str(para) + ': ' + str(value))
    def output(self):
        return self.para_list

class Player(object):
    @classmethod
    def draw(self, mess):
        img = mess['img']
        frame_id = mess['frame_id']
        vehicle_data = mess['vehicle']
        lane_data = mess['lane']
        ped_data = mess['ped']
        tsr_data = mess['tsr']
        can_data = mess.get('can')
        extra = mess['extra']
        mobile_log = extra.get('mobile_log')

        if config.show.overlook:
            DrawOverlook.init(img)

        if config.show_parameters:
            DrawParameters.init(img)
            DrawParameters.draw_env(img, frame_id, vehicle_data,lane_data, extra)
            if config.mobile.show:
                DrawParameters.draw_mobile(img, mobile_log)
        
        if config.show.vehicle:
            DrawVehicle.draw(img, vehicle_data)
        
        if config.show.lane:
            DrawLane.draw(img, lane_data)

        if config.show.ped:
            DrawPed.draw(img, ped_data)

        if config.show.tsr:
            DrawTsr.draw(img, tsr_data)

        if config.can.use and can_data:
            DrawExtra.draw_byd_can(img, can_data, lane_data)

        if config.debug:
            DrawExtra.draw_extra(img, extra)

        return img


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

    @classmethod
    def init(self, img):
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

    @classmethod
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

        roi_img = img[y_begin: y_end, x_begin: x_end]
        cv2.addWeighted(car, 0.5, roi_img, 1.0, 0.0, roi_img)

    @classmethod
    def draw_lane(self, img, ratios, color):
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
    

class DrawParameters(object):
    '''
    画左上角的参数
    '''
    @classmethod
    def init(self, img):
        if config.mobile.show:
            bg_width = 120 * 6
        elif len(config.msg_types) == 1: 
            bg_width = 120 * len(config.msg_types) + 300
        else:
            bg_width = 120 * len(config.msg_types) + 50
        BaseDraw.draw_alpha_rect(img, (0, 0, bg_width+20, 150), 0.4)

        

    @classmethod
    def draw_normal_parameters(self, img, para_list, point):
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

    @classmethod
    def draw_env(self, img, frame_id, vehicle_data, lane_data, extra):
        light_mode = '-'
        if vehicle_data:
            light_mode = vehicle_data['light_mode']
        speed = vehicle_data.get('speed')*3.6 if vehicle_data.get('speed') else 0
        if not speed:
            speed = lane_data.get('speed') if lane_data.get('speed') else speed
        fps = extra.get('fps')
        if not fps:
            fps = 0
        para_list = ParaList('env')
        para_list.insert('speed', int(speed))
        para_list.insert('light', light_mode)
        para_list.insert('fps', fps)
        para_list.insert('fid', frame_id)
        self.draw_normal_parameters(img, para_list, (2, 0))

    @classmethod
    def draw_mobile(self, img, mobile_log):
        if mobile_log:
            mobile_ldw, mobile_hw, mobile_fcw, mobile_vb, mobile_hwm = '-', '-', '-', '-', '-'
            mobile_hwm = mobile_log.get('headway_measurement') if mobile_log.get('headway_measurement') else 0
            mobile_hw = 1 if mobile_log.get('sound_type') == 3 else 0
            mobile_fcw = 1 if mobile_log.get('sound_type') == 6 and mobile_log.get('fcw_on') == 1 else 0
            mobile_pcw = 1 if mobile_log.get('sound_type') == 6 and mobile_log.get('peds_fcw') == 1 else 0
            mobile_vb = 1 if mobile_log.get('sound_type') == 5 else 0
            mobile_ldw = mobile_log['left_ldw'] * 2 + mobile_log['right_ldw'] if 'left_ldw' in mobile_log else 0

            para_list = ParaList('mobile')
            para_list.insert('hwm', mobile_hwm)
            para_list.insert('hw', mobile_hw)
            para_list.insert('fcw', mobile_fcw)
            para_list.insert('vb', mobile_vb)
            para_list.insert('ldw', mobile_ldw)
            para_list.insert('pcw', mobile_pcw)
            DrawParameters.draw_normal_parameters(img, para_list, (300, 0))

class DrawVehicle(object):
    # vehicle
    @classmethod
    def draw(self, img, vehicle_data):
        v_type, index, ttc, fcw ,hwm, hw, vb = '-','-','-','-','-','-','-'
        if vehicle_data:
            focus_index = vehicle_data['focus_index']
            for i, vehicle in enumerate(vehicle_data['dets']):
                focus_vehicle = (i == focus_index)
                position = vehicle['bounding_rect']
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Red if focus_index == i else CVColor.Cyan
                self.draw_vehicle_rect(img, position, color, 2)
                
                self.draw_vehicle_info(img, position,
                                        vehicle['vertical_dist'],vehicle['horizontal_dist'], 
                                        vehicle['vehicle_width'], str(vehicle['type']))
                if config.show.overlook:
                    DrawOverlook.draw_vehicle(img, focus_vehicle,
                                                vehicle['vertical_dist'],
                                                vehicle['horizontal_dist'])
                
            if focus_index != -1:
                vehicle = vehicle_data['dets'][focus_index]
                # v_type = vehicle['type']
                # index = vehicle['index']
                ttc = '%.2f' % vehicle['rel_ttc']
                fcw = vehicle_data['forward_collision_warning']
                hw = vehicle_data['headway_warning']
                hwm = '%.2f' % vehicle_data['ttc']
                vb = vehicle_data['bumper_warning']
                if ttc == '1000.00':
                    ttc = '-'
        
        if config.show_parameters:
            para_list = ParaList('vehicle')
            #para_list.insert('ttc', ttc)
            para_list.insert('fcw', fcw)
            para_list.insert('hwm', hwm)
            para_list.insert('hw', hw)
            para_list.insert('vb', vb)
            DrawParameters.draw_normal_parameters(img, para_list, (100, 0))
        '''
        parameters = [str(v_type), str(index), str(ttc), str(fcw), str(hwm), str(hw), str(vb)]
        self.player.show_vehicle_parameters(img, parameters, (100, 0))
        '''

    @classmethod
    def draw_vehicle_rect(self, img, position, color=CVColor.Cyan, thickness = 2):
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
        BaseDraw.draw_rect_corn(img, (x1, y1), (x2, y2), color, thickness)

    @classmethod
    def draw_vehicle_info(self, img, position, vertical_dis, horizontal_dis, vehicle_width, vehicle_type):
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

class DrawLane(object):

    @classmethod
    def draw(self, img, lane_data):
        lw_dis, rw_dis, ldw, trend = '-', '-', '-', '-'
        if lane_data:
            speed = lane_data['speed']
            deviate_state = lane_data['deviate_state']
            for lane in lane_data['lanelines']:
                if ((int(lane['label']) in [1, 2]) or config.show.all_laneline) and speed >= config.show.lane_speed_limit:
                    # color = CVColor.Cyan
                    color = CVColor.Blue
                    width = lane['width']
                    l_type = lane['type']
                    conf = lane['confidence']
                    index = lane['label']
                    if config.show.lane_begin == -1:
                        begin = int(lane['end'][1])
                    else:
                        begin = config.show.lane_begin
                    if config.show.lane_end == -1:
                        end = int(lane['start'][1])
                    else:
                        end = config.show.lane_end
                    #print('label', index, deviate_state)
                    if int(index) == int(deviate_state):
                        color = CVColor.Red
                    #self.player.show_lane(img, lane['perspective_view_poly_coeff'], 
                    #                      0.2, color, config.show.lane_begin, config.show.lane_end)
                    perspective_view_fitpts = lane.get('perspective_view_fitpts')
                    if perspective_view_fitpts is not None:
                        BaseDraw.draw_polylines(img, perspective_view_fitpts, color, 0.2)
                    else:
                        self.draw_lane_line(img, lane['perspective_view_poly_coeff'], 
                                          0.2, color, begin, end) 
                    #self.draw_lane_info(img, lane['perspective_view_poly_coeff'],
                    #                           index, width, l_type, conf, color)
                    if config.show.overlook:
                        DrawOverlook.draw_lane(img, lane['bird_view_poly_coeff'], color)
                    

            lw_dis = '%.2f' % (lane_data['left_wheel_dist'])
            rw_dis = '%.2f' % (lane_data['right_wheel_dist'])
            ldw = lane_data['deviate_state']
            trend = lane_data['deviate_trend']
            if lw_dis == '111.00':
                lw_dis = '-'
            if rw_dis == '111.00':
                rw_dis = '-'

        if config.show_parameters:
            para_list = ParaList('lane')
            para_list.insert('lw_dis', lw_dis)
            para_list.insert('rw_dis', rw_dis)
            para_list.insert('ldw', ldw)
            #para_list.insert('trend', trend)
            DrawParameters.draw_normal_parameters(img, para_list, (192, 0))
        '''
        parameters = [str(lw_dis), str(rw_dis), str(ldw), str(trend)]
        self.player.show_lane_parameters(img, parameters, (200, 0))
        '''
    @classmethod
    def draw_lane_line(self, img, ratios, width, color, begin=450, end=720):
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

        for y in range(begin, end, 20):
            y1 = y
            y2 = y1 + 20
            x1 = (int)(a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1)
            x2 = (int)(a0 + a1 * y2 + a2 * y2 * y2 + a3 * y2 * y2 * y2)            
            BaseDraw.draw_line(img, (x1, y1), (x2, y2), color, width)
    
    @classmethod
    def draw_lane_info(self, img, ratios, index, width, type, conf, color):
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

class DrawPed(object):
    @classmethod
    def draw(self, img, ped_data):
        pcw_on, ped_on = '-', '-'
        if ped_data:
            if ped_data.get('pcw_on'):
                pcw_on = 1
            if ped_data.get('ped_on'):
                ped_on = 1
            for pedestrain in ped_data['pedestrians']:
                position = pedestrain['regressed_box']
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Yellow
                if pedestrain['is_key']:
                    color = CVColor.Pink
                if pedestrain['is_danger']:
                    color = CVColor.Pink
                self.draw_ped_rect(img, position, color, 2)
                if position[0] > 0:
                    self.draw_ped_info(img, position, pedestrain['dist'])
        if config.show_parameters:
            para_list = ParaList('ped')
            para_list.insert('pcw_on', pcw_on)
            #para_list.insert('ped_on', ped_on)
            DrawParameters.draw_normal_parameters(img, para_list, (430, 0))

    @classmethod
    def draw_ped_rect(self, img, position, color=CVColor.Cyan, thickness = 2):
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
    
    @classmethod
    def draw_ped_info(self, img, position, distance):
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

class DrawTsr(object):
    @classmethod
    def draw(self, img, tsr_data):
        focus_index, speed_limit, tsr_warning_level, tsr_warning_state = -1, 0, 0, 0
        if tsr_data:
            focus_index = tsr_data['focus_index']
            speed_limit = tsr_data['speed_limit']
            tsr_warning_level = tsr_data['tsr_warning_level']
            tsr_warning_state = tsr_data['tsr_warning_state']
            for i, tsr in enumerate(tsr_data['dets']):
                position = tsr['position']
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Red
                self.draw_tsr_rect(img, position, color, 2)
                if tsr['max_speed'] != 0:
                    self.draw_tsr_info(img, position, tsr['max_speed'])                

        if config.show_parameters:
            para_list = ParaList('tsr')
            para_list.insert('speed_limit', speed_limit)
            DrawParameters.draw_normal_parameters(img, para_list, (305, 0))

    @classmethod
    def draw_tsr_rect(self, img, position, color=CVColor.Cyan, thickness = 2):
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
    
    @classmethod
    def draw_tsr_info(self, img, position, max_speed):
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

class DrawExtra(object):

    @classmethod
    def draw_extra(self, img, extra):
        cv2.putText(img, str(extra.get('image_path')), (20, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    @classmethod
    def draw_byd_can(self, img, can_data, lane_data):
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

    
