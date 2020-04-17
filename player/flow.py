from .ui import BaseDraw, CVColor
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

        self.avg = sum / (len(self._l))
        return self.avg

    def get_avg(self):
        return self.avg


class FlowPlayer(object):
    def __init__(self, cfg={}):
        self.cfg = cfg
        self.sys_cpu_avg = Avg(10)
        self.rotor_cpu_avg = Avg(10)

    def draw(self, mess, img):
        if 'pedestrians' in mess:
            res_list = mess['pedestrians']
            for i, obj in enumerate(res_list):
                pos = obj.get('regressed_box')
                color = CVColor.Yellow
                BaseDraw.draw_obj_rect_corn(img, pos, color, 2)

                para_list = [
                    # # 'dist:'+"%.2f" % obj.get('dist'],
                    # 'ttc:' + "%.2f" % obj.get('ttc'),
                    # # 'hit_type:'+str(obj.get('hit_type']),
                    # 'confidence:' + str(obj.get('confidence')),
                    # 'world_x:' + "%.2f" % obj.get('world_x'),
                    # 'world_y:' + "%.2f" % obj.get('world_y'),
                    # # 'ground_y:'+"%.2f" % obj.get('ground_y'],
                    # # 'get_close:'+str(obj.get('get_close']),
                    # 'is_danger:' + str(obj.get('is_danger')),
                    # 'is_key:' + str(obj.get('is_key')),
                    # 'predicted:'+str(obj.get('predicted']),
                    # 'id:' + str(obj.get('id'))
                ]
                # BaseDraw.draw_head_info(img, pos[0:2], para_list, 150)

        if 'vehicle_measure_res_list' in mess:
            res_list = mess['vehicle_measure_res_list']
            for i, vehicle in enumerate(res_list):
                # BaseDraw.draw_obj_rect(img, vehicle['det_rect'], CVColor.Cyan, 1)
                pos = vehicle['reg_rect']
                color = CVColor.Yellow
                BaseDraw.draw_obj_rect_corn(img, pos, color, 2)

                vid = vehicle['vehicle_id']
                vehicle_width = "%.2f" % vehicle.get('vehicle_width', 0)
                ttc = "%.2f" % vehicle.get('ttc', 0)
                d1 = vehicle['longitude_dist']
                d2 = vehicle['lateral_dist']
                d1 = 'nan' if isnan(d1) else int(float(d1) * 100) / 100
                d2 = 'nan' if isnan(d2) else int(float(d2) * 100) / 100
                tid = str(vehicle['vehicle_class'])
                para_list = [
                    'v:' + str(d1),
                    # 'h:' + str(d2),
                    # 'width:' + vehicle_width,
                    # 'type:' + str(VehicleType.get(tid)),
                    'vid:' + str(vid)
                ]
                if vehicle.get('is_crucial'):
                    para_list.append('ttc:' + ttc)
                BaseDraw.draw_head_info(img, pos[0:2], para_list, 85)

        if 'can' in mess:
            DrawAlarmCan.draw(img, mess['can'])

        lanelines = None
        if 'lane' in mess:
            lanelines = mess['lane']
        elif 'lane_warning_res' in mess:  # 新字段
            lanelines = mess['lane_warning_res']['lanelines']
        if lanelines is not None:
            speed = 3.6 * float(mess.get('speed', 0))
            speed_limit = self.cfg.get('lane_speed_limit', 0)
            # print('speed:', speed, speed_limit)
            lane_begin = self.cfg.get('lane_begin', 0)
            for lane in lanelines:
                if ((int(lane['label']) in [1, 2])) and speed >= speed_limit:
                    index = lane['label']
                    begin = lane_begin or int(lane['end'][1])
                    end = int(lane['start'][1])
                    begin = max(begin, 0)
                    end = min(end, 720)

                    color = CVColor.Yellow
                    if self.cfg.get('lane_pts'):
                        BaseDraw.draw_polylines(img, lane['perspective_view_pts'], color, 2)
                    else:
                        BaseDraw.draw_lane_line(img, lane['perspective_view_poly_coeff'],
                                                0.2, color, begin, end)

        if self.cfg.get('show_ultrasonic', 1):
            dis = "-"
            if 'ultrasonic' in mess:
                if self.cfg.get("is_single_ultrasonic", 0):
                    if mess['ultrasonic']['can_id'] == 1281:
                        self.ultrasonic_pair[0] = mess['ultrasonic']
                    elif mess['ultrasonic']['can_id'] == 1282:
                        self.ultrasonic_pair[1] = mess['ultrasonic']

                    if self.ultrasonic_pair[0] and self.ultrasonic_pair[1]:
                        if self.ultrasonic_pair[0]['distance'] and self.ultrasonic_pair[1]['distance']:
                            dis = min(self.ultrasonic_pair[0]['distance'], self.ultrasonic_pair[1]['distance'])
                        else:
                            dis = max(self.ultrasonic_pair[0]['distance'], self.ultrasonic_pair[1]['distance'])
                        dis = round(dis, 2)
                        self.ultrasonic_pair = [{}, {}]
                else:
                    dis = round(mess['ultrasonic']['distance'], 2)
            para_list = [
                # "can_id:%d" % mess['ultrasonic']['can_id'],
                "distance:" + '%sm' % str(dis)
                # 'ts:' + "%.2fs" % (mess['ultrasonic']['time'] / 1000000)
            ]
            BaseDraw.draw_single_info(img, (1100, 0), 120, 'ultrasonic', para_list)
        return img

def chr(d):
    if d < 0:
        return '-'
    return str(d)


class DrawAlarmCan(object):
    '''
    突出显示报警提示, can数据
    '''

    @classmethod
    def draw(self, img, info):
        # info = mess['info']
        info1 = {
            "hw_on": 1,
            "ldw_on": 1,
            "lld": 1,
            "rld": 1,
        }
        fcw, = dict2list(info, ['fcw', ], int, -1)
        ped_on, pcw_on = dict2list(info, ['ped_on', 'pcw_on'], int, -1)
        hw_on, hw = dict2list(info, ['hw_on', 'hw'], int, -1)
        ttc, = dict2list(info, ['ttc'], float, -1)
        ldw_on, lld, rld, lldw, rldw = dict2list(info, ['ldw_on', 'lld', 'rld', 'lldw', 'rldw'], int, -1)
        tsr, = dict2list(info, ['overspeed'], int, -1)
        buzzing, = dict2list(info, ['buzzing'], str, '')
        camera, = dict2list(info, ['camera', ], int, -1)

        ttc = "%2.1f" % ttc if hw > 0 else "-"
        lldw = 2 if lld == 0 else lldw
        rldw = 2 if rld == 0 else rldw

        basex, basey, width, height = (730, 0, 250, 150)
        size, thickness = (0.6, 1)
        alarms = [
            ["CAM:" + chr(camera), 1, (0, 18), int(camera > 0), size, thickness],
            ["FCW:" + chr(fcw), 1, (0, 18), int(fcw > 0), size, thickness],
            ["HWM:" + chr(hw) + "  ttc:" + ttc + "  on:" + chr(hw_on), 1, (0, 18), int(hw > 1), size, thickness],
            ["PCW:" + chr(pcw_on) + "  ped:" + chr(ped_on), 1, (0, 18), int(pcw_on > 0), size, thickness],
            ["TSR: " + chr(tsr), 1, (0, 18), int(tsr > 10), size, thickness],
            ["AW :" + buzzing, 1, (0, 18), int(bool(buzzing)), size, thickness],
            ["|", 1, (0, 30), lldw, 1, 2],
            ["|", 1, (50, 0), rldw, 1, 2],
            ["on:" + chr(ldw_on), 1, (50, 0), int(ldw_on > 0), size, thickness],
        ]

        color = [CVColor.Green, CVColor.Red, CVColor.White]  # 不报警 报警
        BaseDraw.draw_alpha_rect(img, (basex - 10, basey, width, height), 0.4)
        x, y = (basex, basey)
        for alarm in alarms:
            text, show, pos, value, size, thickness = alarm
            if show:
                x += pos[0]
                y += pos[1]
                BaseDraw.draw_text(img, text, (x, y), size, color[value], thickness)

        BaseDraw.draw_text(img, "(can)", (basex, y + 25), 0.4, CVColor.Yellow, 1)


def dict2list(d, keys, type=None, default=None):
    values = []
    for key in keys:
        value = d.get(key, default)
        if type:
            value = type(value)
        values.append(value)
    return values
