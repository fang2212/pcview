# from math import fabs, sin, cos, pi
from math import *


class CIPOFilter(object):
    def __init__(self):
        self.cipo = {}
        self.last_id = -1

    def update(self, obs):
        ret = False
        # print(obs['id'])
        if obs['id'] < self.last_id:
            self.cipo.clear()
        self.last_id = obs['id']
        if -1.8 <= obs['pos_lat'] <= 1.8:
            # if len(cipo) == 0 or cipo['pos_lon'] > obs['pos_lon']:
            self.cipo[obs['id']] = {}
            self.cipo[obs['id']]['pos_lat'] = obs['pos_lat']
            self.cipo[obs['id']]['pos_lon'] = obs['pos_lon']
            obs_list = sorted(self.cipo, key=lambda x: self.cipo[x]['pos_lon'])
            # print(obs_list)
            if len(obs_list) > 0 and obs['id'] == obs_list[0]:
                ret = True

        return ret

    def add_cipo(self, obslist):
        valid = [obs for obs in obslist if -1.8 <= obs['range'] * sin(obs['angle'] * pi / 180.0) <= 1.8]
        sobs = sorted(valid, key=lambda x: x['range'])
        if len(sobs) == 0:
            cipo_id = -1
        else:
            cipo_id = sobs[0]['id']
        ret = []
        for obs in obslist:
            if obs.get('id'):
                if obs['id'] == cipo_id:
                    obs['cipo'] = True
                ret.append(obs)
        return ret


def is_near(data0, data1):
    if 'range' in data0 and 'angle' in data0:
        range0 = data0.get('range')
        angle0 = data0.get('angle')
        x0 = range0 * cos(angle0 * pi / 180.0)
        y0 = range0 * sin(angle0 * pi / 180.0)
    else:
        x0 = data0.get('pos_lon')
        y0 = data0.get('pos_lat')
        angle0 = atan2(y0, x0) * 180.0 / pi
        range0 = (x0 ** 2 + y0 ** 2) ** 0.5

    if 'range' in data1 and 'angle' in data1:
        range1 = data1.get('range')
        angle1 = data1.get('angle')
        x1 = range1 * cos(angle1 * pi / 180.0)
        y1 = range1 * sin(angle1 * pi / 180.0)
    else:
        x1 = data1.get('pos_lon')
        y1 = data1.get('pos_lat')
        angle1 = atan2(y1, x1) * 180.0 / pi
        range1 = (x1 ** 2 + y1 ** 2) ** 0.5

    if 'range_rate' in data0:
        vx0 = data0.get('range_rate')
    else:
        vx0 = data0.get('vel_lon')
    if 'range_rate' in data1:
        vx1 = data1.get('range_rate')
    else:
        vx1 = data1.get('vel_lon')
    ts0 = data0.get('ts')
    ts1 = data1.get('ts')

    # x1 = range1 * cos(angle1 * pi / 180.0)
    # y1 = range1 * sin(angle1 * pi / 180.0)

    # return y0 - 3.6 < y1 < y0 + 3.6 and x0 - 2.8 < x1 < x0 + 2.8
    if fabs(range0 - range1) > 18:
        # print('range too large', data0['id'], data1['id'], fabs(range0 - range1))
        return False
    if fabs(angle0 - angle1) > 2:
        # print('angle too large', data0['id'], data1['id'], fabs(angle0 - angle1))
        return False
    # if fabs(ts0 - ts1) > 0.2:
    # print('time diff too large', fabs(ts0 - ts1))
    # return False
    # print(data0, data1, vx0, vx1)
    # if fabs(vx0 - vx1) > 3:
    #     return False
    return True