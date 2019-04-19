import time
import cantools
from math import *

# db_x1 = cantools.database.load_file('dbc/MINIEYE_CAR.dbc', strict=False)
# db_x1.add_dbc_file('dbc/MINIEYE_PED.dbc')
# db_x1.add_dbc_file('dbc/MINIEYE_LANE.dbc')
db_x1 = cantools.database.load_file('dbc/AEB_20181203.dbc', strict=False)
# db_x1.add_dbc_file('dbc/ESR DV3_64Tgt.dbc')

cipv = {}
x1_ped = {}
x1_obs = {}

def parse_x1(id, data):
    ids = [m.frame_id for m in db_x1.messages]
    if id not in ids:
        return None
    r = db_x1.decode_message(id, data)
    # print("0x%x" % id, r)
    if id == 0x76d:
        # print("0x%x" % id, r)
        if r['TargetVehicleType'] == 'No Vehicle':
            return None
        else:
            # print("0x%x" % id, r)
            cipv['type'] = 'obstacle'
            cipv['cipo'] = True
            cipv['id'] = r['TargetID']
            cipv['pos_lat'] = r['TargetVehiclePosY']
            cipv['pos_lon'] = r['TargetVehiclePosX']
            cipv['color'] = 4
            cipv['class'] = r['TargetVehicleType']
            # return {'type': 'obstacle','id': r['TargetID'], 'pos_lat': r['TargetVehiclePosY'], 'pos_lon': r['TargetVehiclePosX'], 'color': 3}
    if id == 0x76e:
        if len(cipv) == 0:
            return None
        cipv['width'] = r['TargetVehicleWidth']
        cipv['confi'] = r['TargetVehicleConfidence']
        cipv['vel_lon'] = r['TargetVehicleVelX']
        # cipv['TTC'] = r['TTC']
        obs = cipv.copy()
        cipv.clear()

        return obs

    if 0x770 <= id <= 0x777:
        index = id - 0x770 + 1
        obs_num = r['AdditionTargetNumber' + str(index)]
        x1_obs_list = []
        for i in range(obs_num):
            x1_obs['type'] = 'obstacle'
            x1_obs['id'] = r['Target' + str(2 * (index - 1) + i + 1) + '_ID']
            x1_obs['class'] = r['AdditionVehicle' + str(2 * (index - 1) + i + 1) + '_Type']
            x1_obs['pos_lon'] = r['AdditionVehicle' + str(2 * (index - 1) + i + 1) + '_PosX']
            x1_obs['pos_lat'] = r['AdditionVehicle' + str(2 * (index - 1) + i + 1) + '_PosY']
            x1_obs['ttc'] = 7
            x1_obs['vel_lon'] = 0
            x1_obs['cipv'] = 0
            x1_obs['color'] = 3
            x1_obs['width'] = 2
            x1_obs_list.append(x1_obs.copy())
            x1_obs.clear()

        return x1_obs_list

    if id == 0x77a:
        cipv['width'] = 0.3
        cipv['type'] = 'obstacle'
        cipv['cipo'] = True
        cipv['id'] = r['Target_Pedestrian_ID']
        cipv['vel_lon'] = r['Target_Pedestrian_VelX']
        cipv['pos_lat'] = r['Target_Pedestrian_PosY']
        cipv['pos_lon'] = r['Target_Pedestrian_PosX']
        cipv['color'] = 4
        cipv['class'] = r['Target_Pedestrian_Type']
        # cipv['TTC'] = r['TTC']
        if cipv['pos_lon'] > 0:
            ped = cipv.copy()
            cipv.clear()
            return ped
        else:
            return None

    if 0x77b <= id <= 0x77d:
        index = id - 0x77a
        ped_num = r['Addition_Pedestrian_Number' + str(index)]
        x1_ped_list = []
        for i in range(ped_num):
            x1_ped['width'] = 0.3
            x1_ped['cipo'] = 0
            x1_ped['id'] = r['Addition_Pedestrian_' + str(2 * (index - 1) + i + 1) + '_ID']
            x1_ped['class'] = r['Target_Pedestrian_' + str(2 * (index - 1) + i + 1) + '_Type']
            x1_ped['pos_lon'] = r['Addition_Pedestrian_' + str(2 * (index - 1) + i + 1) + '_PosX']
            x1_ped['pos_lat'] = r['Addition_Pedestrian_' + str(2 * (index - 1) + i + 1) + '_PosY']
            x1_ped['type'] = 'obstacle'
            x1_ped['color'] = 3
            x1_ped['vel_lon'] = 0
            x1_ped_list.append(x1_ped.copy())
            x1_ped.clear()
        return x1_ped_list