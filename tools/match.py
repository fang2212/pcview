from math import fabs, sin, cos, pi

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
            if obs['id'] == cipo_id:
                obs['cipo'] = True
            ret.append(obs)
        return ret


def is_near(data0, data1):
    range0 = data0.get('range')
    angle0 = data0.get('angle')
    range1 = data1.get('range')
    angle1 = data1.get('angle')
    ts0 = data0.get('ts')
    ts1 = data1.get('ts')
    x0 = range0 * cos(angle0 * pi / 180.0)
    y0 = range0 * sin(angle0 * pi / 180.0)
    x1 = range1 * cos(angle1 * pi / 180.0)
    y1 = range1 * sin(angle1 * pi / 180.0)

    # return y0 - 3.6 < y1 < y0 + 3.6 and x0 - 2.8 < x1 < x0 + 2.8
    if fabs(range0-range1) > 2.5:
        return False
    if fabs(angle0-angle1) > 3.0:
        return False
    if fabs(ts0 - ts1) > 0.2:
        return False

    return True