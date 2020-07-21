from tools.geo import *
import json


class RoadExp(object):
    lanes = []
    traffic_signs = []

    def __init__(self, roi):
        self.lat0, self.lon0, self.lat1, self.lon1 = roi

    def update_lane(self, pos_body, lane_para):
        a0, a1, a2, a3 = lane_para

    def update_traffic_sign(self, tsr):
        id = tsr.get('id')
        name = tsr.get('sign_name')
        conf = tsr.get('confidence')
        # x = tsr.get('pos_lat')
        # y = tsr.get('pos_lon')
        # h = tsr.get('pos_hgt')
        lat = tsr.get('lat')
        lon = tsr.get('lon')
        hgt = tsr.get('hgt')
        print('updated tsr: {id} {name} at {lat} {lon} {hgt}'.format(**tsr))
        self.traffic_signs.append(tsr)

    def dump(self, fp):
        items = {'start_lat': self.lat0, 'start_lon': self.lon0, 'end_lat': self.lat1, 'end_lon': self.lon1,
                 'lanes': self.lanes, 'traffic_signs': self.traffic_signs}

        json.dump(items, fp, indent=True)

    def load(self, fp):
        items = json.load(fp)
        self.lat0 = items['start_lat']
        self.lon0 = items['start_lon']
        self.lat1 = items['end_lat']
        self.lon1 = items['end_lon']

    def covers(self, lat, lon):
        if self.lat0 < lat < self.lat1 and self.lon0 < lon < self.lon1:
            return True

