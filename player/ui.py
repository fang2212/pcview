import os
import cv2
from datetime import datetime
import numpy as np


def dict2list(d, keys, type=None, default=None):
    values = []
    for key in keys:
        value = d.get(key, default)
        if type:
            value = type(value)
        values.append(value)
    return values


VehicleType = {
    '1': 'car',
    '2': 'minibus',
    '3': 'bus',
    '4': 'truck',
    '5': 'ssp'
}


class CVColor(object):
    '''
    basic color RGB define
    '''
    Aqua = (255, 255, 0)
    Red = (0, 0, 255)
    Peru = (63, 133, 205)
    Chocolate = (30, 105, 210)
    LightRed = (80, 80, 200)
    MediumBlue = (205, 0, 0)
    Green = (0, 255, 0)
    Crimson = (60, 20, 220)        # 深红色
    LightCoral = (128, 128, 240)        # 淡珊瑚色
    MediumTurquoise = (204, 209, 72)  # 中绿宝石色
    Grass = (0x50, 0xaf, 0x4c)
    DeepSkyBlue = (255, 191, 0)
    Blue = (255, 0, 0)
    LightBlue = (240, 120, 120)
    Cyan = (0xd4, 0xbc, 0)
    Magenta = (255, 0, 255)
    Yellow = (0, 255, 255)
    Black = (0, 0, 0)
    White = (255, 255, 255)
    Grey = (120, 120, 120)
    Midgrey = (160, 160, 160)
    LightGray = (211, 211, 211)
    Pink = (255, 0, 255)
    indigo = (0xb5, 0x51, 0x3f)
    purple = (0xb0, 0x27, 0x9c)
    bluegrey = (0x8b, 0x7D, 0x60)
    deeporange = (0x1a, 0xbc, 0xff)
    SandyBrown = (96, 164, 244)
    NavajoWhite = (173, 222, 255)
    DarkMagenta = (139, 0, 139)
    Linen = (230, 240, 250)


class FlatColor(object):  # in BGR
    Blue = (200, 0, 0)
    Beige = (220, 245, 245)                 # 米黄色
    Green = (0, 255, 0)                     # 绿色
    LightPink = (193, 182, 255)             # 浅粉红
    alizarin = (0x3c, 0x4c, 0xe7)
    amethyst = (0xb6, 0x59, 0x9b)
    carrot = (0x22, 0x7e, 0xe6)
    clouds = (0xf1, 0xf0, 0xec)
    concrete = (0xa6, 0xa5, 0x95)
    dark_red = (0x10, 0x10, 0x80)
    emerald = (0x71, 0xcc, 0x2e)
    violet = (255, 0, 255)                  # 紫色
    light_green = (154, 255, 154)           # 淡绿色
    light_blue = (255, 225, 202)            # 淡蓝色
    peter_river = (0xdb, 0x98, 0x34)
    pink = (166, 171, 248)                  # 粉色
    peach = (157, 153, 245)                 # 桃色
    sun_flower = (0x0f, 0xc4, 0xf1)
    turquoise = (0x9c, 0xa0, 0x16)
    yellow_green = (112, 255, 202)          # 黄绿色
    yellow = (57, 171, 242)                 # 黄色
    moccasin = (191, 236, 212)
    lightcoral = (152, 151, 255)
    mediumpurple = (189, 134, 158)
    wet_asphalt = (0x5e, 0x49, 0x34)


color_dict = {
    "a1j": (59, 59, 238),
    "a1j_fusion": (59, 59, 238),
    "a1j_vision": (193, 182, 255),
    "ars410": FlatColor.peach,
    "bosch_mrr": FlatColor.yellow,
    "bosch_f": FlatColor.mediumpurple,
    "bosch_r": FlatColor.mediumpurple,
    "bosch_fr": FlatColor.mediumpurple,
    "bosch_fl": FlatColor.mediumpurple,
    "bosch_rr": FlatColor.mediumpurple,
    "bosch_rl": FlatColor.mediumpurple,
    "d1_fusion": FlatColor.violet,
    "gs4_debug": FlatColor.pink,
    "j2": FlatColor.carrot,
    "j2_fusion": FlatColor.light_green,
    "q4_100": FlatColor.turquoise,
    "wsk": FlatColor.Green,
    "wsk_old": FlatColor.pink,
    'anc': FlatColor.carrot,
    'ars': FlatColor.emerald,
    'ars_back': FlatColor.emerald,
    'ctlrr': FlatColor.alizarin,
    'default': FlatColor.clouds,
    'esr': FlatColor.alizarin,
    'gps': FlatColor.clouds,
    'ifv300': CVColor.Blue,
    'ifv300_fusion': CVColor.Blue,
    'ifv300_vision': (255, 144, 30),
    'lmr': FlatColor.emerald,
    'lhgd': FlatColor.yellow,
    'mbq3': CVColor.Blue,
    'mbq3_fusion': CVColor.Blue,
    'mbq3_vision': (255, 144, 30),
    'mbq4': FlatColor.turquoise,
    "mu_f": CVColor.Aqua,
    "mu_fr": CVColor.Aqua,
    "mu_fl": CVColor.Aqua,
    "mu_r": CVColor.Aqua,
    "mu_rr": CVColor.Aqua,
    "mu_rl": CVColor.Aqua,
    'q3': CVColor.Blue,
    'rtk': FlatColor.sun_flower,
    'sta77': FlatColor.wet_asphalt,
    'x1': FlatColor.amethyst,
    'x1_fusion': CVColor.Red,
    'x1_fusion_cam': FlatColor.dark_red,
    'x1j': FlatColor.amethyst,
    'xyd2': FlatColor.Blue,
}


class FPSCnt(object):

    def __init__(self, period, fps):
        self.period = period
        self.start_time = None
        self.cnt = 0
        self.fps = fps
    
    def inc(self, step=1):
        if self.cnt % self.period == 0:
            if not self.start_time:
                self.start_time = datetime.now()
            else:
                temp = self.start_time
                self.start_time = datetime.now()
                delta = (self.start_time - temp).total_seconds()
                print('fps period:', self.period, 'delta:', delta)
                self.fps = str("%.2f" % (self.period / delta))
        self.cnt += step

class BaseDraw(object):
    """
    基本的opencv绘图函数
    """

    @classmethod
    def draw_circle(cls, img, position, radius=4, color=CVColor.Black):
        cv2.circle(img, position, radius, color)

    @classmethod
    def draw_up_arrow(cls, img, x, y, color=CVColor.White, w=8, thickness=2):

        cv2.line(img, (x, y), (x - w, y + w), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x, y), (x + w, y + w), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x, y), (x, y + 2 * w), color, thickness, cv2.LINE_8, 0)


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
    def draw_obj_rect(self, img, position, color=CVColor.Cyan, thickness = 2):
        """绘制pedestrain
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            color: CVColor 颜色
            thickness: int 线粗
        """
        x1, y1, width, height = list(map(int, position))
        BaseDraw.draw_rect(img, (x1, y1), (x1+width, y1+height), color, thickness)

    @classmethod
    def draw_rect_corn(cls, img, point1, point2, color, thickness=2, len_ratio=6):
        """
            draw 8 lines at corns
        """
        x1, y1 = point1
        x2, y2 = point2
        width = abs(x2-x1)
        height = abs(y2-y1)
        suit_len = min(width, height)
        suit_len = int(suit_len / len_ratio)
        # print('suit_len', suit_len)
        
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
    def show_stop_wall(self, img, pt1, pt2, color, thickness=2):
        pt3 = (pt1[0], pt2[1])
        pt4 = (pt2[0], pt1[1])
        cv2.rectangle(img, pt1, pt2, color, thickness)
        cv2.line(img, pt1, pt2, color, thickness)
        cv2.line(img, pt3, pt4, color, thickness)

    @classmethod
    def draw_obj_rect_corn(cls, img, position, color=CVColor.Cyan, thickness=2, len_ratio=6):
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
        BaseDraw.draw_rect_corn(img, (x1, y1), (x2, y2), color, thickness, len_ratio)

    @classmethod
    def draw_line(cls, img_content, p1, p2,  color_type = CVColor.White, thickness=1, type=cv2.LINE_8):
        cv2.line(img_content, p1, p2, color_type, thickness, type, 0)

    @classmethod
    def draw_lane_line(cls, img, ratios, width, color, begin=450, end=720):
        """绘制车道线
        Args:
            img: 原始图片
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * x + a2 * x^2 * y1 + a3 * x^3
            width: float 车道线宽度
            color: CVColor 车道线颜色
        """
        if np.NaN in ratios:
            return
        try:
            a0, a1, a2, a3 = list(map(float, ratios))
        except Exception as e:
            return
        width = int(float(width) * 10 + 0.5)
        for y in range(begin, end, 20):
            y1 = y
            y2 = y1 + 20
            x1 = (int)(a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1)
            x2 = (int)(a0 + a1 * y2 + a2 * y2 * y2 + a3 * y2 * y2 * y2)            
            cls.draw_line(img, (x1, y1), (x2, y2), color, width)

    @classmethod
    def draw_lane_lines(cls, img, lanelines, speed, deviate_state, lane_begin=0, draw_all=False, speed_limit=30):
        for lane in lanelines:
            if ((int(lane['label']) in [1, 2]) or draw_all) and speed >= speed_limit:
                # width = lane['width']
                # l_type = lane['type']
                # conf = lane['confidence']
                index = lane['label']
                begin = lane_begin or int(lane['end'][1])
                end = int(lane['start'][1])
                if end > 720:
                    end = 720
                if begin < 0:
                    begin = 0
                
                color = CVColor.Blue
                if 'warning' in lane:
                    if lane['warning'] and int(index) == int(deviate_state):
                        color = CVColor.Red

                # perspective_view_pts = lane.get('perspective_view_pts')
                perspective_view_pts = None
                if perspective_view_pts:
                    cls.draw_polylines(img, perspective_view_pts, color, 2)
                else:
                    cls.draw_lane_line(img, lane['perspective_view_poly_coeff'],
                                       0.2, color, begin, end)

    @classmethod
    def draw_alpha_rect(cls, image_content, rect, alpha, color=CVColor.Black, line_width=0):
        x, y, w, h = rect
        mask = np.zeros((h, w, 3), np.uint8)
        mask[:] = color
        # mask = np.full((h, w), color)
        roi = image_content[y:y+h, x:x+w]
        cv2.addWeighted(mask, alpha, roi, 1.0-alpha, 0.0, roi)
        if line_width > 0:
            cv2.rectangle(image_content, (x, y), (x+w, y+h), color, line_width)

    @classmethod
    def draw_alpha_poly(cls, image_content, poly, alpha, color=CVColor.Black):
        # x, y, w, h = rect
        # if not isinstance(poly, np.array):
        #     print('input param poly must be numpy array.')
        #     return
        # print(image_content.shape, )
        xmin = np.min(poly[:, 0])
        # print(xmin)
        # xmin = np.max(xmin, 0)
        ymin = np.min(poly[:, 1])
        # ymin = np.max(ymin, 0)
        xmax = np.max(poly[:, 0])
        # xmax = np.min(xmax, image_content.shape[0])
        ymax = np.max(poly[:, 1])
        # ymax = np.min(ymax, image_content.shape[1])
        poly[:, 0] -= xmin
        poly[:, 1] -= ymin
        mask = image_content[ymin:ymax, xmin:xmax].copy()
        cv2.fillConvexPoly(mask, poly, color)

        # mask = np.full((h, w), color)
        roi = image_content[ymin:ymax, xmin:xmax]
        cv2.addWeighted(mask, alpha, roi, 1.0 - alpha, 0.0, roi)

    @classmethod
    def draw_polylines(cls, img, pts, color, thickness=2):
        '''
        :param pts: 三维数组 [ line, ... ], line: [ point, ... ], point: [x,y]
        '''
        nts = []
        for i, pt in enumerate(pts):
            p0, p1 = pt
            nts.append([int(p0), int(p1)])
        pts = [nts]
        pts = np.array(pts)
        cv2.polylines(img, pts, False, color, thickness)

    @classmethod
    def draw_single_info(self, img, point, width, title, para_list):
        """显示物体头部信息 for car & ped
        Args:
            img: 原始图片
            point: 左上角位置
            para_list: List [index, TODO ]
        """
        x, y = int(point[0]), int(point[1])
        num = len(para_list)
        gap_v = 18
        size = 0.5

        rect = (x, y, width, (num+1)*gap_v+6)
        BaseDraw.draw_alpha_rect(img, rect, 0.2)
        BaseDraw.draw_text(img, title, (x+5, y+gap_v), size, CVColor.Cyan, 1)
        BaseDraw.draw_para_list(img, (x+5, y+gap_v*2), para_list, gap_v, size)

    @classmethod
    def draw_head_info(cls, img, point, para_list, width=120, max_range=[1280, 720]):
        """显示物体头部信息 for car & ped
        Args:
            img: 原始图片
            point: 左上角位置
            para_list: List [index, TODO ]
        """
        x, y = int(point[0]), int(point[1])
        num = len(para_list)
        gap_v = 18
        size = 0.5

        if y - num * gap_v - 6 < 0:
            y = num * gap_v + 6
        elif y >= max_range[1]:
            y = max_range[1]

        if x + width >= max_range[0]:
            x = max_range[0] - width
        if x < 0:
            x = 0

        rect = (x, y - num * gap_v - 6, width, num * gap_v + 6)
        BaseDraw.draw_alpha_rect(img, rect, 0.4)
        BaseDraw.draw_para_list(img, (x + 5, y - 6), para_list, -gap_v, size)

    @classmethod
    def draw_lane_warnning(cls, img, point, warning):
        """显示车道线报警
        """
        warning = int(warning)
        left_color, right_color = CVColor.White, CVColor.White
        if warning == 1:
            left_color = CVColor.Red
        if warning == 2:
            right_color = CVColor.Red
        if warning == 5:
            left_color = CVColor.Yellow
        if warning == 6:
            right_color = CVColor.Yellow
        BaseDraw.draw_text(img, '|', point, 2, left_color, 3)
        BaseDraw.draw_text(img, '|', (point[0]+50, point[1]), 2, right_color, 3)

    @classmethod
    def draw_para_list(cls, img, point, para_list, gap_v=20, size=0.5):
        """显示参数信息
        Args:
            img: 原始图片
            point: 起点位置
            para_list: List [index, TODO ]
        """
        origin_x, origin_y = int(point[0]), int(point[1])
        for index, para in enumerate(para_list): 
            BaseDraw.draw_text(img, para,
                               (origin_x, origin_y + gap_v * index),
                               size, CVColor.White, 1)



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

    @classmethod
    def init(self, img):
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
            BaseDraw.draw_line(img, (x1, y1), (x2, y2), CVColor.Cyan, 1)