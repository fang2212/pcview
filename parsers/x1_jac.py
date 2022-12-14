#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import cantools

db_d1 = cantools.database.load_file('dbc/MINIEYE_X1J-JAC_GREENCAR_CAN_20210225.dbc', strict=False)

jac = {}
cipp = {}
d1_lane = {}
spp_lane = {}


def parse_x1_jac(id, data, ctx=None):
    ids = [m.frame_id for m in db_d1.messages]
    if id not in ids:
        return None
    r = db_d1.decode_message(id, data)

    if not ctx.get('x1_jac'):
        ctx['x1_jac'] = list()

    if 0x76d <= id <= 0x76f:
        # print("0x%x" % id, r)
        if len(jac) >= 7:
            jac.clear()

        if id == 0x76e:
            jac["TTC"] = r["TargetVehicle_TTC"]
        elif id == 0x76d:
            jac['pos_lat'] = r['TargetVehicle_PosY']
            jac['pos_lon'] = r['TargetVehicle_PosX']
            jac["id"] = r["Vehicle_ID"]
            r = jac.copy()
            r["type"] = "obstacle"
            return r
        elif id == 0x76f:
            jac["speed"] = r["speed"]

        if len(jac) == 5:
            jac["type"] = "vehicle_state"
            jac['sensor'] = 'x1_jac'
            # print(jac)
            return jac.copy()

