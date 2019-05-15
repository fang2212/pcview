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
        valid = [obs for obs in obslist if -1.8 <= obs['pos_lat'] <= 1.8]
        sobs = sorted(valid, key=lambda x: x['pos_lon'])
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
