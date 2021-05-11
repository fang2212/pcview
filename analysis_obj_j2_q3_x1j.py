#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file    :   analysis_obj_j2_q3_x1j.py    
@contact :   caofulin@minieye.cc
@date    :   2021/1/18 下午7:49
"""
from parsers.j2 import parser_j2
from parsers.x1j import parse_x1j
from parsers.mobileye_q3 import parse_ifv300
from tools.log_info import get_can_ports_and_roles
from parsers.parser import parsers_dict

import sys
import matplotlib.pyplot as plt


def run(log):

    ctx = get_can_ports_and_roles(log)
    can_ports = dict([val, key] for key,val in ctx['can_port'].items())

    can_ctx = {'j2': {}, 'x1j': {}, 'ars': {}, 'ifv300': {}}
    can_res = {'j2': [], 'x1j': [], 'ars': [], 'ifv300': []}

    lane_res = {'j2': [[], []], 'x1j': [[], []], 'ars': [[], []], 'ifv300': [[], []]}

    flag = 0
    with open(log, "r") as rf:
        for line in rf:
            line = line.strip()
            fields = line.split()
            if "camera" in line:
                fid = int(fields[-1])
                if fid >= 59750:
                    flag = 1
            if not flag:
                continue
            ts = float(fields[0]) + float(fields[1]) / 1000000
            if 'CAN' in line:
                can_id = int(fields[3], 16)
                data = bytes().fromhex(fields[4])

                can_msg = can_ports[fields[2]]
                parse = parsers_dict[can_msg]

                ret = None
                ret = parse(can_id, data, can_ctx[can_msg])
                if ret is None:
                    continue
                ret = [ret] if type(ret) == dict else ret

                for o in ret:
                    if 'type' not in o: continue
                    if o['type'] == "lane":
                        if o['id'] < 2:
                            lane_res[can_msg][o['id']].append((ts, o))

                    elif o['type'] == "obstacle" and "cipo" in o and o['cipo']:
                        can_res[can_msg].append((ts, o))
        return can_res, lane_res


def plot_compare(data):
    color = {"j2": "r", "ifv300": "b", "x1j": "y", "ars": "g"}
    for key in data:
        x = [ i[0] for i in data[key]]
        offset = 0
        if key == "j2":
            offset = 3.66
        y = [ i[1]["pos_lon"] - offset for i in data[key]]
        plt.plot(x, y, label=key, color=color[key])

    plt.legend()
    plt.show()
    plt.clf()


def plot_lane(data):
    color = {"j2": "r", "ifv300": "b", "x1j": "y", "ars": "g"}
    fig, axs = plt.subplots(4, 1, sharex=True)

    for key in data:
        idx = 1
        if key == "ifv300":
            idx = 1 - idx

        x = [ o[0] for o in data[key][idx] ]
        y = [ o[1]['a0'] for o in data[key][idx] ]
        axs[0].plot(x, y, label=key, color=color[key])
        axs[0].set_title("a0")
        axs[0].legend()

        y = [o[1]['a1'] for o in data[key][idx]]
        axs[1].plot(x, y, label=key, color=color[key])
        axs[1].set_title("a1")
        axs[1].legend()

        y = [o[1]['a2'] for o in data[key][idx]]
        axs[2].plot(x, y, label=key, color=color[key])
        axs[2].set_title("a2")
        axs[2].legend()

        y = [o[1]['a3'] for o in data[key][idx]]
        axs[3].plot(x, y, label=key, color=color[key])
        axs[3].set_title("a3")
        axs[3].legend()

    plt.show()


if __name__ == '__main__':
    import json, os
    sys.argv.append("/home/cao/桌面/ftmp/20210114112824白天静止目标测试/log_sort.txt")

    if os.path.exists(os.path.dirname(sys.argv[1]) +"/res.tmp.json"):
        res, lane_res = json.load(open(os.path.dirname(sys.argv[1]) +"/res.tmp.json", "r"))
    else:
        res, lane_res = run(sys.argv[1])
        json.dump([res, lane_res], open(os.path.dirname(sys.argv[1]) + "/res.tmp.json", "w"), indent=2)
    print( [ (key, len(res[key])) for key in res])

    plot_lane(lane_res)
    # plot_compare(res)