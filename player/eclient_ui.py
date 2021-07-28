import eclient
import numpy as np
import sharemem

from player.ui import CVColor


eClient = eclient.ElectronClient()
eClient.connect()
view2D = eClient.getPluginByName('plugin-2DView')
if not view2D:
    print('Error: cannot find plugin-2DView')
    exit(1)

mem_info = eClient.getSharedMemoryInfo()
mem = sharemem.ShareMem(mem_info['name'], mem_info['size'])
mem.open()

request = eClient.createPluginRequest([view2D])
request.clearAll()

class CVColor(object):
    '''
    basic color RGB define
    '''
    Red = "rgb(255, 0, 0)"
    LightRed = "rgb(200, 80, 80)"
    Green = "rgb(0, 255, 0)"
    Grass = "rgb(76, 175, 80)"
    Blue = "rgb(0, 0, 255)"
    LightBlue = "rgb(120, 120, 240)"
    Cyan = "rgba(0, 188, 212)"
    Magenta = "rgb(255, 0, 255)"
    Yellow = "rgb(255, 255, 0)"
    Black = "rgba(0,0,0,0.5)"
    White = "rgb(255, 255, 255)"
    Grey = "rgb(120, 120, 120)"
    Midgrey = "rgb(160, 160, 160)"
    LightGray = "rgb(211, 211, 211)"
    Pink = "rgb(255, 0, 255)"
    indigo = "rgb(63, 81, 181)"
    purple = "rgb(156, 39, 176)"
    bluegrey = "rgb(96, 125, 139)"
    deeporange = "rgb(255, 188, 26)"

class FlatColor(object):  # in BGR
    Blue = "rgb(0, 0, 200)"
    alizarin = "rgb(231, 76, 60)"
    amethyst = "rgb(155, 89, 182)"
    carrot = "rgb(230, 126, 34)"
    clouds = "rgb(236, 240, 241)"
    concrete = "rgb(149, 165, 166)"
    dark_red = "rgb(128, 16, 16)"
    emerald = "rgb(46, 204, 113)"
    violet = "rgb(255, 0, 255)"                  # 紫色
    light_green = "rgb(154, 255, 154)"           # 淡绿色
    light_blue = "rgb(202, 225, 255)"            # 淡蓝色
    peter_river = "rgb(52, 152, 219)"
    pink = "rgb(248, 171, 166)"                  # 粉色
    peach = "rgb(245, 153, 157)"                 # 桃色
    sun_flower = "rgb(241, 196, 15)"
    turquoise = "rgb(22, 160, 156)"
    yellow_green = "rgb(112, 255, 202)"          # 黄绿色
    yellow = "rgb(242, 171, 57)"                 # 黄色
    wet_asphalt = "rgb(52, 73, 94)"

class BaseDraw(object):
    """
    基本的绘图函数
    """
    @classmethod
    def covert_alpha(cls, color, alpha=None):
        if alpha is not None:
            color = color[:3] + "a" + color[3:-2] + "," + str(alpha) + ")"
        return color

    @classmethod
    def draw_img(cls, img):
        """
        绘制图片画面
        :param img:
        :return:
        """
        image = eClient.createAttachment('shared-memory')
        offset = image.allocForWriting(len(img))
        mem.write_memory(offset, img)
        image.finishWriting()
        request.drawImage(image, 'jpg')

    # **************************** 状态框 ****************************

    @classmethod
    def draw_status_indent(cls, position, radius=5, color=CVColor.White):
        request.drawShape({
            'type': 'POINTS',
            'coords': position,
            'options': {
                'shape': 'rect',  # 点的形状：矩形
                'fill': color,
                'radius': radius,
            }
        })

    @classmethod
    def draw_circle(cls, position, radius=20, color="", border_color="", thickness=5):
        """
        绘制圆
        :param img:
        :param position:
        :param radius:
        :param color:
        :return:
        """
        request.drawShape({
            'type': 'CIRCLE',
            'options': {
                'center': position,             # 圆心
                'radius': radius,                   # 半径
                'stroke': border_color,         # 线的颜色
                'strokeWidth': thickness,       # 线的粗细
                'fill': color,                  # 填充色
            }
        })

    @classmethod
    def draw_arrow(cls, top, end, color="", border_color="", border_width="", head_width="", head_length="", tail_width=""):
        """
        绘制箭头
        :param top: 头部尖端点
        :param end: 尾部中心点
        :param color: 填充色
        :param border_color: 边框颜色
        :param border_width: 边框宽度
        :param tail_width: 尾部长度（默认）
        :param head_width: 头部宽度（默认）
        :param head_length: 头部长度（默认）
        :return:
        """
        request.drawShape({
            'type': 'ARROW',
            'coords': [
                end[0], end[1],  # 尾部中心点
                top[0], top[1],  # 头部尖端点
            ],
            'options': {
                'headLength': head_length,  # 头部长度（默认）
                'headWidth': head_width,   # 头部宽度（默认）
                'tailWidth': tail_width,   # 尾部宽度（默认）
                'stroke': border_color,
                'strokeWidth': border_width,
                'fill': color,
            },
        })

    @classmethod
    def draw_text(cls, text, position, size, color=CVColor.White, thickness=1):
        """
        For anti-aliased text, add argument cv2.LINE_AA.
        sample drawText(img_content, text, (20, 30), 0.6, CVColor.Blue, 2)
        """
        request.drawShape({
            'type': 'TEXT',
            'text': text,
            'options': {
                'position': position,  # 文本位置
                'fontSize': size,  # 字体大小
                'fill': color,  # 字体颜色
                "strokeWidth": thickness,   # 字体粗细
            },
        })

    @classmethod
    def draw_rect(cls, point1, point2, color=None, border=None, border_color=None):
        request.drawShape({
            'type': 'RECT',
            'coords': [
                point1[0],  point1[1],  # 左上角(x, y)
                point2[0], point2[1],  # 右下角(x, y)
            ],
            'options': {
                'stroke': border_color,    # 边框颜色
                "strokeWidth": border,  # 边框粗细
                'fill': color,  # 矩形的填充色
            },
        })

    @classmethod
    def draw_obj_rect(self, img, position, color=CVColor.Cyan, thickness=2):
        """绘制pedestrain
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            color: CVColor 颜色
            thickness: int 线粗
        """
        pass

    @classmethod
    def draw_rect_corn(cls, img, point1, point2, color, thickness=2, len_ratio=6):
        """
            绘制矩形四角框
        """
        x1, y1 = point1
        x2, y2 = point2
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        suit_len = min(width, height)
        suit_len = int(suit_len / len_ratio)
        request.drawShape({
            'type': 'RECT_CORNER',  # 角线的长度默认10像素
            "coords": [
                x1, y1,
                x2, y2,
            ],
            'options': {
                "cornerSize": suit_len,
                "stroke": color,
                "strokeWidth": thickness,  # 字体粗细
            },
        })

    @classmethod
    def show_stop_wall(self, img, pt1, pt2, color, thickness=2):
        pass

    @classmethod
    def draw_obj_rect_corn(cls, img, position, color=CVColor.Cyan, thickness=2, len_ratio=6):
        """绘制车辆框
        Args:
            img: 原始图片
            position: (x, y, width, height),车辆框的位置，大小
            color: CVColor 车辆颜色
            thickness: int 线粗
        """
        pass

    @classmethod
    def draw_line(cls, img_content, ratios, start=0, end=0, dash=None, color=CVColor.White, thickness=1):
        request.drawShape({
            'type': 'POLYNOMIAL_CURVE',
            'coeff': ratios,  # y = c0+c1*x+c2*x^2+c3*x^3
            'options': {
                'dash': dash,  # 虚线的每一小段（实、虚）的长度
                'independent': 'x',  # x坐标作为自变量
                'dependent': 'y',    # y坐标作为因变量
                'independentRange': [start, end],  # 自变量的范围
                'sampleRate': 5,   # 自变量的采样率（每隔多少像素采样一个点）
                'stroke': color,   # 线的颜色
                'strokeWidth': thickness,  # 线的粗细
            },
        })

    @classmethod
    def draw_quadratic_curve(cls, point_list, color=CVColor.White, thickness=1):
        draw_list = np.array(point_list, int)
        coords = draw_list.flatten()
        request.drawShape({
            'type': 'QUADRATIC_CURVE',
            'coords': coords.tolist(),
            'options': {
                'stroke': color,    # 曲线的颜色
                'fill': '',        # 填充色
                'strokeWidth': thickness,  # 线的粗细
            },
        })

    @classmethod
    def draw_polyline(cls, point_list, dash='', color=CVColor.White, thickness=1):
        draw_list = np.array(point_list, int)
        coords = draw_list.flatten()
        request.drawShape({
            'type': 'POLYLINE',
            'coords': coords.tolist(),
            'options': {
                'dash': dash,  # 虚线的每一小段（实、虚）的长度
                'stroke': color,  # 曲线的颜色
                'fill': '',  # 填充色
                'strokeWidth': thickness,  # 线的粗细
            },
        })

    @classmethod
    def draw_lane_line(cls, img, ratios, width, color, begin=450, end=720):
        """绘制车道线
        Args:
            img: 原始图片
            ratios:List [a0, a1, a2, a3] 车道线参数 y = a0 + a1 * x + a2 * x^2 * y1 + a3 * x^3
            width: float 车道线宽度
            color: CVColor 车道线颜色
        """
        pass

    @classmethod
    def draw_lane_lines(cls, img, lanelines, speed, deviate_state, lane_begin=0, draw_all=False, speed_limit=30):
        pass

    @classmethod
    def draw_alpha_rect(cls, image_content, rect, color=CVColor.Black, border_color="", line_width=0):
        x, y, w, h = rect
        request.drawShape({
            'type': 'RECT',
            'coords': [
                x,  y,  # 左上角(x, y)
                x+w, y+h,  # 右下角(x, y)
            ],
            'options': {
                'stroke': border_color,    # 无边框
                'strokeWidth': line_width,  # 边框的粗细
                'fill': color,  # 矩形的填充色
            },
        })

    @classmethod
    def draw_alpha_poly(cls, image_content, poly, alpha, color=CVColor.Black):
        pass

    @classmethod
    def draw_polylines(cls, img, pts, color, thickness=2):
        '''
        :param pts: 三维数组 [ line, ... ], line: [ point, ... ], point: [x,y]
        '''
        pass

    @classmethod
    def draw_single_info(self, img, point, width, title, para_list):
        """显示物体头部信息 for car & ped
        Args:
            img: 原始图片
            point: 左上角位置
            para_list: List [index, TODO ]
        """
        pass

    @classmethod
    def draw_head_info(cls, img, point, para_list, width=120, max_range=[1280, 720]):
        """显示物体头部信息 for car & ped
        Args:
            img: 原始图片
            point: 左上角位置
            para_list: List [index, TODO ]
        """
        pass

    @classmethod
    def draw_lane_warnning(cls, img, point, warning):
        """显示车道线报警
        """
        pass

    @classmethod
    def draw_para_list(cls, img, point, para_list, gap_v=20, size=0.5):
        """显示参数信息
        Args:
            img: 原始图片
            point: 起点位置
            para_list: List [index, TODO ]
        """
        pass

    @classmethod
    def submit(cls):
        eClient.submitPluginRequests([request])

    @classmethod
    def clear(cls):
        request.clearAll()