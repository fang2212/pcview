#!/usr/bin/env python
# _*_ coding:utf-8 _*_
from math import sqrt, pi, atan2

import cantools

bosch_db = cantools.database.load_file('dbc/FR5CP_SFCAN_Matrix_V1_20201202_Released.dbc', strict=False)

cipv = {}
cipp = {}
x1_lane = {}
detection_sensor = {
    0: 'no_matched_measurements',
    1: 'single_radar_only',
    2: 'multi_radar_only',
    3: 'vision_only',
    4: 'radar and vision',
}

mrr_status = {}

def bosch_mrr(cid, data, ctx=None):
    ids = [m.frame_id for m in bosch_db.messages]
    if cid not in ids:
        return None
    r = bosch_db.decode_message(cid, data)
    if ctx and ctx.get('parser_mode') == 'direct':
        return r
    # print("0x%x" % id, r)
    if not ctx.get('bosch_obs'):
        ctx['bosch_obs'] = list()
    if cid == 0x200:
        mrr_status["status"] = r["FR5CP_FailureStatus"]

    if 0x203 <= cid <= 0x20a:
        # other car
        index = cid - 0x203
        # 因中间少了个0x207，所以后面的需要做一下特殊处理
        index = index - 1 if index > 4 else index

        start_num = index * 5 + 1
        end_num = 33 if index == 6 else start_num + 5
        for i in range(start_num, end_num):
            if r["FR5CP_ObjExistProb_{}".format(i)] > 0:
                data = {
                    "source": ctx["source"],
                    'type': 'obstacle',
                    'sensor': 'bosch',
                    'sensor_type': 'radar',
                    'id': r["FR5CP_ObjID_{}".format(i)],
                    'pos_lon': r["FR5CP_ObjDistX_{}".format(i)],
                    'pos_lat': -r["FR5CP_ObjDistY_{}".format(i)],
                    'vel_lon': r["FR5CP_ObjRelVelX_{}".format(i)],
                    'vel_lat': -r["FR5CP_ObjRelVelY_{}".format(i)],
                }
                # data['range'] = sqrt(data['pos_lon']**2 + data['pos_lat']**2)
                data['angle'] = atan2(data['pos_lat'], data['pos_lon']) * 180 / pi
                ttc = data['pos_lon'] / -data['vel_lon'] if data['vel_lon'] < 0 else 7
                if ttc > 7:
                    ttc = 7
                # 状态框显示信息
                data["status_show"] = [
                    {"text": "status:{}".format(mrr_status.get("status", "Failure"))}
                    # {"text": "TTC:{:.2f}s".format(ttc)},
                    # {"text": 'R/A: {:.2f} / {:.2f}'.format(data["pos_lon"], data['angle'])}
                ]
                ctx['bosch_obs'].append(data)

        if cid == 0x20a:
            r = ctx['bosch_obs'].copy()
            ctx['bosch_obs'].clear()
            return r


if __name__ == "__main__":
    bosch_mrr(0x20a, bytes().fromhex("00000002004010068032000000000002004010068032000000000000000794e4"), {})
    # parse_bosch(0x209, bytes().fromhex("00000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000076d89"), {})
    # parse_bosch(0x206, bytes().fromhex("00000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000000002004010068032000000076d89"), {})