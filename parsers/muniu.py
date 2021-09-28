#!/usr/bin/env python
# _*_ coding:utf-8 _*_
from math import sqrt, pi, atan2

import cantools

mn_db = cantools.database.load_file('dbc/20210813_T79.dbc', strict=False)

mn_ids = [m.frame_id for m in mn_db.messages]


def parser_mu_f(cid, data, ctx=None):
    if cid not in mn_ids:
        return None
    r = mn_db.decode_message(cid, data)

    # print("0x%x" % id, r)
    if not ctx.get('mn_f_obs'):
        ctx['mn_f_obs'] = list()
    if cid == 0x4b1:
        return {'type': 'status', "status_show": [{"text": "FL_speed:{}km/h".format(r["RadarSubVehicle_Speed"]), "height": 40}]}
    elif cid == 0x4b2:
        return {'type': 'status', "status_show": [{"text": "FR_speed:{}km/h".format(r["RadarSubVehicle_Speed"]), "height": 60}]}


def parser_mu_r(cid, data, ctx=None):
    if cid not in mn_ids:
        return None
    r = mn_db.decode_message(cid, data)

    # print("0x%x" % id, r)
    if not ctx.get('mn_r_obs'):
        ctx['mn_r_obs'] = list()
    if cid == 0x4b3:
        return {'type': 'status', "status_show": [{"text": "FL_speed:{}km/h".format(r["RadarSubVehicle_Speed"]), "height": 40}]}
    elif cid == 0x4b4:
        return {'type': 'status', "status_show": [{"text": "FR_speed:{}km/h".format(r["RadarSubVehicle_Speed"]), "height": 60}]}



if __name__ == "__main__":
    parser_mu_r(0x20a, bytes().fromhex("a601ee81fb7fa080"), {})
