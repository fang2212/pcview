#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import cantools
db_spp = cantools.database.load_file('dbc/SPP_CAN_v96.dbc', strict=False)

spp_lane = {}
def parser_gs4(id, buf, ctx=None):

    ids = [m.frame_id for m in db_spp.messages]
    if id not in ids:
        return None

    r = db_spp.decode_message(id, buf, decode_choices=False)

    # int:281
    if id == 0x119:
        spp_lane["range"] = r["SPP_max_range"]
        spp_lane["min_range"] = r["SPP_min_range"]

    # 车中线 int:289
    if id == 0x121:
        return {
            "type": "lane",
            "type_class": "spp:{}".format(spp_lane.get('range', 50)),
            "range": spp_lane.get('range', 50),
            "a0": r["SPP_POLY_COEFF_A0"],
            "a1": r["SPP_POLY_COEFF_A1"],
            "a2": r["SPP_POLY_COEFF_A2"],
            "a3": r["SPP_POLY_COEFF_A3"],
            "style": spp_lane.get("style")
        }

    # 车中线显示状态 int:2019
    elif id == 0x7e3:
        spp_lane["style"] = "" if r["LCK_Mode"] == 4 else "dotted"  # 正常显示为直线，否则虚线

