#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import cantools
db_spp = cantools.database.load_file('dbc/SPP_CAN_v96.dbc', strict=False)

spp_lane = {}
spp_statue = {}
spp_type = ["Invalid", "LLM_Only", "RLM_Only", "BLM_Only", "PO_Only", "PO_and_LLM", "PO_and_RLM", "PO_and_BLM", "Reserved"]


def parser_gs4(id, buf, ctx=None):

    ids = [m.frame_id for m in db_spp.messages]
    if id not in ids:
        return None

    r = db_spp.decode_message(id, buf, decode_choices=False)

    if id == 0x111:
        spp_statue["lt"] = r["LLM_status"]
    elif id == 0x114:
        spp_statue["po_st"] = r["PO_status"]
        spp_statue["po_type"] = r["PO_type"]
        spp_statue["po_conf"] = r["PO_conf"]
    elif id == 0x115:
        spp_statue["pid"] = r["PO_fusTrackId"]
        spp_statue["lat"] = r["PO_lat_pos"]
        spp_statue["lng"] = r["PO_lng_pos"]
    elif id == 0x117:
        spp_statue["rl"] = r["RLM_status"]

    # int:281
    elif id == 0x119:
        spp_lane["range"] = r["SPP_max_range"]
        spp_lane["min_range"] = r["SPP_min_range"]

        spp_statue["bl"] = r["BLM_Status"]

        return {
            "type": "status",
            "source": ctx.get("source"),
            "status_show": [
                {"text": "Spp Type:{}".format(spp_type[r["SP_type"]])},
                {"text": "Spp st:{}, conf:{}".format(r["SP_status"], r["SP_conf"])},
                {"text": "LT:{}  RT:{}  BL:{}".format(spp_statue.get("lt", 0), spp_statue.get("rt", 0), spp_statue.get("bl", 0))},
                {"text": "PO id:{}, st:{}".format(spp_statue.get("pid", 0), spp_statue.get('po_st', 0))},
                {"text": "PO type:{}, conf:{}".format(spp_statue.get("po_type", 0), spp_statue.get('po_conf', 0))},
                {"text": "R:{}".format(spp_statue.get("R", 0))},
                {"text": "lat:{}".format(spp_statue.get("lat", 0))},
                {"text": "lng:{}".format(spp_statue.get("lng", 0))}
            ]
        }

    # 车中线 int:289
    elif id == 0x121:
        spp_statue['R'] = 1/(2*r["SPP_POLY_COEFF_A2"])
        if spp_statue['R'] > 10000:
            spp_statue['R'] = 10000
        elif spp_statue['R'] < -10000:
            spp_statue['R'] = -10000

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

