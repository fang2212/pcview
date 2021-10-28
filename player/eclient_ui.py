import numpy as np

from player.eclient_websock_api import EClientApi
from player.ui import CVColor
from sink.eclient_websockets import Server
from sink.mmap_queue import MMAPQueue
from utils import logger

recv_queue = MMAPQueue(1024*1024*3)
send_queue = MMAPQueue(1024*1024*3)

# eclient_server = Server(recv_queue=recv_queue)
# eclient_server.start()
eclient_server = None


class BaseDraw(object):
    """
    基本的绘图函数
    """

    @classmethod
    def init(cls):
        global eclient_server
        try:
            eclient_server = EClientApi(plugin_title_list=['video-main', 'front-ipm', 'video-sub1', 'video-sub2', 'video-sub3'],
                       msg_queue=send_queue)
            eclient_server.daemon = True
            eclient_server.start()
        except Exception as e:
            logger.exception(e)

    # **************************** 事件方法 ****************************

    @classmethod
    def get_event(cls):
        return recv_queue.get(block=False)

    # **************************** 颜色处理方法 ****************************

    @classmethod
    def covert_alpha(cls, color, alpha=None):
        if alpha is not None:
            color = color[:3] + "a" + color[3:-2] + "," + str(alpha) + ")"
        return color


    @classmethod
    def bgr_to_str(cls, color, alpha=None):
        if alpha is None:
            color = f"rgb({color[2]}, {color[1]}, {color[0]})"
        else:
            color = f"rgba({color[2]}, {color[1]}, {color[0]}, {alpha})"
        return color

    # **************************** 布局类方法 ****************************

    @classmethod
    def draw_img(cls, img, plugin_name='video-main'):
        """
        绘制图片画面
        :param plugin_name: 画板插件名
        :param img:
        :return:
        """
        eclient_server.send_data({
            'type': 'img',
            'data': img,
            'plugin': plugin_name
        })

    @classmethod
    def draw_status_indent(cls, position, radius=5, color=CVColor.White, plugin_name='video-main'):
        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
                'type': 'POINTS',
                'coords': position,
                'options': {
                    'shape': 'rect',  # 点的形状：矩形
                    'fill': color,
                    'radius': radius,
                }
            }
        })

    @classmethod
    def draw_ipm(cls):
        """
        俯视图背景
        :return:
        """
        pass

    # **************************** 组件类方法 ****************************

    @classmethod
    def draw_grid_3d(cls, plugin_name='front-ipm'):
        # front_ipm_request.drawShape({
        #     'type': 'GRID_3D',
        #     'option': {
        #         'rows': 15,             # 横向格子数
        #         'cols': 15,             # 纵向格子数
        #         'cellSize': 4,          # 格子大小
        #         'position': [0, 0, 0],  # 中心点的坐标
        #         'rotation': [0, 0, 0],  # 旋转角度（欧拉角）
        #         'camera': {
        #             'fovx': 85,   # 摄像机的X方向视角（默认根据Y方向视角fovy和画布宽高比aspect自动算出）
        #             'position': [0, 4, 10],
        #             'rotation': [-5, 0, 0],  # pitch: -5d
        #         },
        #         'stroke': 'gray',
        #         'strokeWidth': 1,
        #     },
        #
        # })
        pass

    @classmethod
    def draw_circle(cls, position, radius=20, color="", border_color="", thickness=5, plugin_name='video-main'):
        """
        绘制圆
        :param img:
        :param position:
        :param radius:
        :param color:
        :return:
        """
        if isinstance(color, tuple):
            color = BaseDraw.bgr_to_str(color)
        if isinstance(border_color, tuple):
            border_color = BaseDraw.bgr_to_str(border_color)
        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
                'type': 'CIRCLE',
                'options': {
                    'center': position,             # 圆心
                    'radius': radius,                   # 半径
                    'stroke': border_color,         # 线的颜色
                    'strokeWidth': thickness,       # 线的粗细
                    'fill': color,                  # 填充色
                }
            }
        })

    @classmethod
    def draw_arrow(cls, top, end, color="", border_color="", border_width="", head_width="", head_length="", tail_width="", plugin_name='video-main'):
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
        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
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
            }
        })

    @classmethod
    def draw_text(cls, text, position, size, color=CVColor.White, thickness=1, plugin_name='video-main'):
        """
        For anti-aliased text, add argument cv2.LINE_AA.
        sample drawText(img_content, text, (20, 30), 0.6, CVColor.Blue, 2)
        """
        if isinstance(color, tuple):
            color = BaseDraw.bgr_to_str(color)

        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
                'type': 'TEXT',
                'text': text,
                'options': {
                    'position': position,  # 文本位置
                    'fontSize': size,  # 字体大小
                    'fill': color,  # 字体颜色
                    "strokeWidth": thickness,   # 字体粗细
                },
            }
        })

    @classmethod
    def draw_rect(cls, point1, point2, color=None, thickness=None, border_color=None, plugin_name='video-main'):
        if isinstance(color, tuple):
            color = BaseDraw.bgr_to_str(color)
        if isinstance(border_color, tuple):
            border_color = BaseDraw.bgr_to_str(border_color)
        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
                'type': 'RECT',
                'coords': [
                    point1[0],  point1[1],  # 左上角(x, y)
                    point2[0], point2[1],  # 右下角(x, y)
                ],
                'options': {
                    'stroke': border_color,    # 边框颜色
                    "strokeWidth": thickness,  # 边框粗细
                    'fill': color,  # 矩形的填充色
                },
            }
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
    def draw_rect_corn(cls, img, point1, point2, color, thickness=2, len_ratio=6, plugin_name='video-main'):
        """
            绘制矩形四角框
        """
        if isinstance(color, tuple):
            color = BaseDraw.bgr_to_str(color)
        x1, y1 = point1
        x2, y2 = point2
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        suit_len = min(width, height)
        suit_len = int(suit_len / len_ratio)

        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
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
            }
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
    def draw_line(cls, start, end, dash='', color=CVColor.White, thickness=1, plugin_name='video-main'):
        if isinstance(color, tuple):
            color = BaseDraw.bgr_to_str(color)

        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
                'type': 'LINES',
                'coords': [
                     start[0], start[1], end[0], end[1]
                ],
                'options': {
                    'dash': dash,  # 虚线的每一小段（实、虚）的长度
                    'stroke': color,   # 线的颜色
                    'strokeWidth': thickness,  # 线的粗细
                },
            }
        })

    @classmethod
    def draw_quadratic_curve(cls, point_list, color=CVColor.White, thickness=1, plugin_name='video-main'):
        if isinstance(color, tuple):
            color = BaseDraw.bgr_to_str(color)

        draw_list = np.array(point_list, int)
        coords = draw_list.flatten()

        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
                'type': 'QUADRATIC_CURVE',
                'coords': coords.tolist(),
                'options': {
                    'stroke': color,    # 曲线的颜色
                    'fill': '',        # 填充色
                    'strokeWidth': thickness,  # 线的粗细
                },
            }
        })

    @classmethod
    def draw_polyline(cls, point_list, dash='', color=CVColor.White, thickness=1, plugin_name='video-main'):
        if isinstance(color, tuple):
            color = BaseDraw.bgr_to_str(color)

        draw_list = np.array(point_list, int)
        coords = draw_list.flatten()

        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
                'type': 'POLYLINE',
                'coords': coords.tolist(),
                'options': {
                    'dash': dash,  # 虚线的每一小段（实、虚）的长度
                    'stroke': color,  # 曲线的颜色
                    'fill': '',  # 填充色
                    'strokeWidth': thickness,  # 线的粗细
                },
            }
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
    def draw_alpha_rect(cls, image_content, rect, color='', border_color="", line_width=0, plugin_name='video-main'):
        x, y, w, h = rect
        eclient_server.send_data({
            'plugin': plugin_name,
            'data': {
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
            }
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
        eclient_server.send_data({'type': 'submit'})

    @classmethod
    def clear(cls, plugin):
        eclient_server.send_data({'type': 'clear', "plugin": plugin})

    @classmethod
    def close(cls):
        eclient_server.close()
