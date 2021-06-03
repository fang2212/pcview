#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import cantools
db_spp = cantools.database.load_file('dbc/SPP_CAN_v88.dbc', strict=False)


def parser_gs4(id, buf, ctx=None):

    ids = [m.frame_id for m in db_spp.messages]
    if id not in ids:
        return None

    r = db_spp.decode_message(id, buf, decode_choices=False)

    # if id == 2024:
    #     return r

    # 车中线
    if id == 2028:
        return {
            "type": "lane",
            "type_class": "spp",
            "range": 25,
            "a0": r["SPP_POLY_COEFF_A0"],
            "a1": r["SPP_POLY_COEFF_A1"],
            "a2": r["SPP_POLY_COEFF_A2"],
            "a3": r["SPP_POLY_COEFF_A3"],
        }

