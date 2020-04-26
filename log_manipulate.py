import json
import os
import shutil
import time
from collections import deque
import pickle
from math import *

import cantools
import numpy as np


class bcl:
    HDR = '\033[95m'
    OKBL = '\033[94m'
    OKGR = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


obs_meas_order = ['pos_lat', 'pos_lon', 'vel_lon', 'TTC']
obs_meas_display = ['y', 'x', 'Vx', 'TTC']
obs_meas_lane = ['']


def compose_log(ts, log_type, data):
    tv_s = int(ts)
    tv_us = (ts - tv_s) * 1000000
    log_line = "%.10d %.6d " % (tv_s, tv_us) + log_type + ' ' + data + "\n"
    return log_line



def time_sort(file_name, sort_itv=8000, output=None):
    """
    sort the log lines according to timestamp.
    :param file_name: path of the log file
    :param sort_itv:
    :return: sorted file path

    """
    size = os.path.getsize(file_name)
    out_file = output or '/tmp/log_sort.txt'
    if size < 50 * 1024 * 1024:
        wf = open(out_file, 'w')
        with open(file_name) as rf:
            lines = rf.readlines()
            lines = sorted(lines)
        wf.writelines(lines)
        wf.close()
        # print('sorted', out_file)
        return os.path.abspath(out_file)
        # sort_itv = 8000
    # rev_lines = []
    past_lines = deque(maxlen=2 * sort_itv)
    wf = open(out_file, 'w')
    idx = 0
    with open(file_name) as rf:
        for idx, line in enumerate(rf):
            if line == '\n': continue
            cols = line.split(' ')
            tv_s = int(cols[0])
            tv_us = int(cols[1])
            ts = tv_s * 1000000 + tv_us
            past_lines.append([ts, line])
            # print(len(past_lines))
            if len(past_lines) < 2 * sort_itv:
                continue
            if (idx + 1) % sort_itv == 0:
                # print(len(past_lines))
                past_lines = sorted(past_lines, key=lambda x: x[0])
                wf.writelines([x[1] for x in past_lines[:sort_itv]])
                past_lines = deque(past_lines, maxlen=2 * sort_itv)
            # if len(past_lines) > 300:  # max lines to search forward.
            #     wf.write(past_lines.popleft()[1])
    past_lines = sorted(past_lines, key=lambda x: x[0])
    wf.writelines([x[1] for x in past_lines[sort_itv - ((idx + 1) % sort_itv):]])

    wf.close()
    return os.path.abspath(out_file)


def process_log(file_name, parsers, ctx, startf=None, endf=None, output=None):
    print('processing log: {}'.format(file_name))
    out_file = output or '/tmp/log_processed_{}.txt'.format(int(time.time()))
    wf = open(out_file, 'w')
    if startf is not None and endf is not None:
        pstate = False
    else:
        pstate = True
    with open(file_name) as rf:
        for line in rf:
            # print(line)
            ret_line = None

            if line == '\n':
                continue
            if len(line) < 26:
                continue
            # try:
            log_type = line.split(' ')[2]
            if log_type == 'camera':
                fid = int(line.split(' ')[3])
                # print('fid', fid)
                if startf and endf and startf <= fid <= endf:
                    pstate = True

            if not pstate:
                # print('not pstate')
                continue
            for func in parsers:
                # print(line)
                ret_line = func(line, ctx)
                # print(can_port, buf, r)
                if ret_line and len(ret_line) > 0:
                    # print(ret_line)
                    wf.write(ret_line)
                    break
            # except Exception as e:
            #     print(bcl.FAIL + '[Error]' + bcl.ENDC, e)

            # wf.write(line)
    wf.close()
    return os.path.abspath(out_file)


def strip_log(file_name):
    def strip(line, ctx):
        if line == '\n':
            return None
        elif len(line) < 26:
            return None
        else:
            return line

    r = process_log(file_name, [strip], None)
    return r


def test_sort(file_name):
    last_time = 0
    with open(file_name) as rf:
        for idx, line in enumerate(rf):
            cols = line.split(' ')
            tv_s = int(cols[0])
            tv_us = int(cols[1])
            ts = tv_s * 1000000 + tv_us
            if ts < last_time:
                print('reversed timestamp:line{} {}'.format(idx + 1, ts))
            last_time = ts


def find_frame_jump(file_name, thres=10000):
    last_time = 0
    cnt = 0
    cnt1 = 0
    idx = 0
    with open(file_name) as rf:
        for idx, line in enumerate(rf):
            cols = line.split(' ')
            if cols[2] == 'camera':
                cnt1 += 1
                tv_s = int(cols[0])
                tv_us = int(cols[1])
                ts = tv_s * 1000000 + tv_us
                if last_time == 0:
                    last_time = ts
                    continue
                if ts - last_time > 50000 + thres:
                    # print('line[{}]: found frame jumping. {}'.format(idx+1, (ts-last_time)/1000000))
                    cnt += 1
                last_time = ts
            elif cols[2] == 'cam_frame':
                cnt1 += 1
                tv_s = int(cols[0])
                tv_us = int(cols[1])
                ts = tv_s * 1000000 + tv_us
                if last_time == 0:
                    last_time = ts
                    continue
                if ts - last_time > 50000 + thres:
                    print('{}: found frame jumping. {}'.format(cols[3].strip(), (ts - last_time) / 1000000))
                    cnt += 1
                last_time = ts
    print('found {} jumping frames in total {} frames. {}%'.format(cnt, cnt1, 100 * cnt / cnt1))


def dummy_parser(line, ctx):
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if not ctx.get('ts0'):
        ctx['ts0'] = ts

    # ctx['last_tick'] = ts


def tell_interval(line, ctx):
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000


def copier(line, ctx):
    return line


def align_log(file_name, delay_tbl):
    """
    re-align the log file due to the given delay.
    :param file_name: path of the log file
    :param delay_tbl: pre-defined dict which contains delay param for each log type
    :return: aligned file path
    """
    wf = open('log_align.txt', 'w')
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            type = cols[2]
            delay = delay_tbl.get(type)
            if delay is not None and delay != 0:
                tv_s = int(cols[0])
                tv_us = int(cols[1])
                delay = int(delay)
                ts_new = tv_s * 1000000 + tv_us - delay * 1000
                cols[0] = str(int(ts_new / 1000000))
                cols[1] = '%.6d' % (ts_new % 1000000)
            wf.write(' '.join(cols))
    wf.close()
    return os.path.abspath('log_align.txt')


def clean_esr(file_name):
    """
    strip the no_target ESR lines out of the log file.
    :param file_name: the file path which you want to strip
    :return: striped file path
    """
    wf = open('log_strip.txt', 'w')
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            if cols[2] == 'ESR':
                if int(cols[6], 16) == 0:
                    continue
            wf.write(line)
    wf.close()
    return os.path.abspath('log_strip.txt')


def unify_esr_ts(file_name):
    """
    unify the timestamp of every track in the same epoch.
    :param file_name: the file path which you want to strip
    :return: unified file path
    """
    wf = open('log_unify.txt', 'w')
    epoch_start = None
    last_id = 0x00
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            if cols[2] == 'ESR':
                if epoch_start is None:
                    epoch_start = [cols[0], cols[1]]
                    continue
                id = int(cols[4], 16)
                if id < last_id:
                    epoch_start = [cols[0], cols[1]]
                else:
                    cols[0] = epoch_start[0]
                    cols[1] = epoch_start[1]
                last_id = id
            wf.write(' '.join(cols))
    wf.close()
    return os.path.abspath('log_unify.txt')


def unify_ars_ts(file_name):
    """
        unify the timestamp of every track in the same epoch.
        :param file_name: the file path which you want to strip
        :return: unified file path
    """
    wf = open('log_unify_ars.txt', 'w')
    epoch_start = None

    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            if cols[2] == 'ARS':
                if epoch_start is None:
                    epoch_start = [cols[0], cols[1]]
                    continue
                id = int(cols[4], 16)
                if id == 0x600:
                    epoch_start = [cols[0], cols[1]]
                else:
                    cols[0] = epoch_start[0]
                    cols[1] = epoch_start[1]

            wf.write(' '.join(cols))
    wf.close()
    return os.path.abspath('log_unify_ars.txt')


def rename_log_type(file_name):
    """
        rename the type names in log due to json/can_type.json.
        :param file_name: the file path which you want to deal with
        :return: unified file path
    """
    types = json.load(open('json/can_type.json'))
    # types = {}
    # types['CAN0'] = []
    # types['CAN0'].append({})
    # types['CAN0'].append({})
    # types['CAN0'].append({})
    # types['CAN0'][0]['begin'] = 0x00
    # types['CAN0'][0]['end'] = 0x736
    # types['CAN0'][0]['type_name'] = 'Q3INST'
    # types['CAN0'][1]['begin'] = 0x73c
    # types['CAN0'][1]['end'] = 0x765
    # types['CAN0'][1]['type_name'] = 'Q3INST'
    # types['CAN0'][2]['begin'] = 0x76c
    # types['CAN0'][2]['end'] = 0x7ff
    # types['CAN0'][2]['type_name'] = 'Q3INST'
    # json.dump(types, open('js    with open(file_name) as rf:on/can_type.json', 'w'), indent=True)
    wf = open('log_rename.txt', 'w')
    epoch_start = None
    cnt1 = 0
    cnt2 = 0
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            if cols[2] in types.keys():
                can_id = int(cols[3], 16)
                for type in types[cols[2]]:
                    if type['begin'] <= can_id <= type['end']:
                        cols[2] = type['type_name']
                        cnt1 += 1

            if cols[2] == 'cam_frame':
                cols[3] = cols[3].split('.')[0].split('_')[1] + '\n'
                cnt2 += 1
                cols[2] = 'camera'
            wf.write(' '.join(cols))
    wf.close()
    print('parsed {} CAN frames, {} cam frames'.format(cnt1, cnt2))
    return os.path.abspath('log_rename.txt')


def parse_veh_speed(file_name):
    wf = open('log_speed.txt', 'w')
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            if cols[2] == 'CAN0':
                if cols[3] == "0xCFE6CEE":
                    speed = int(cols[11], 16)
                    shaft = int(cols[9], 16) << 8 | int(cols[8], 16)
                    cols[2] = "speed"
                    cols[3] = str(speed)
                    cols[4] = "shaft"
                    cols[5] = str(shaft) + '\n'
                    cols = cols[:6]
            wf.write(' '.join(cols))
    wf.close()
    return os.path.abspath('log_speed.txt')


def parse_q2_speed(file_name):
    wf = open('log_speed.txt', 'w')
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            if cols[2] == 'CAN1':
                if cols[3] == "0x760":
                    data = [int(x, 16) for x in cols[4:]]
                    left_signal = (data[0] >> 1) & 0x01
                    right_signal = (data[0] >> 2) & 0x01
                    speed = data[2]

                    if left_signal == 1:
                        turnlamp = 1
                    if right_signal == 1:
                        turnlamp = 2
                    else:
                        turnlamp = 0
                    cols[2] = 'speed'
                    cols[3] = str(speed)
                    cols[4] = 'turnlamp'
                    cols[5] = str(turnlamp) + '\n'
                    cols = cols[:6]
                else:
                    continue

            wf.write(' '.join(cols))
    wf.close()
    return os.path.abspath('log_speed.txt')


def parse_q3_speed(file_name):
    db = cantools.database.load_file('/home/nan/workshop/doc/eyeQ3/dbc/INST_CAN_v04.05d_all.dbc', strict=False)
    wf = open('log_speed.txt', 'w')
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            if cols[2] == 'CAN0':
                can_id = int(cols[3], 16)
                if can_id == 0x440:
                    buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                    r = db.decode_message(can_id, buf)
                    speed = r['CAN_VEHICLE_SPEED'] * 3.6
                    cols[2] = 'speed'
                    cols[3] = str(int(speed)) + '\n'
                    cols = cols[:4]
                else:
                    cols[2] = 'Q3INST'
            wf.write(' '.join(cols))
    wf.close()
    return os.path.abspath('log_speed.txt')


def parse_drtk(file_name):
    from parsers.drtk import parse_rtk
    ctx = {}
    wf = open('log_rtk.txt', 'w')
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if 'CAN' in cols[2]:
                can_id = int(cols[3], 16)
                if can_id == 0xc7:
                    if not ctx.get(cols[2]):
                        ctx[cols[2]] = {}
                    buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                    res = parse_rtk(can_id, buf, ctx[cols[2]])
                    if res:
                        if isinstance(res, list):
                            r = res[0]
                            if r.get('type') != 'rtk':
                                continue
                            # print(r)
                            log_type = 'rtk.{}.sol'.format(int(int(cols[2][3]) / 2))
                            data = '{} {} {:.8f} {:.8f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f}'.format(
                                r['rtkst'], r['orist'], r['lat'], r['lon'], r['hgt'], r['velN'],
                                r['velE'], r['velD'], r['yaw'], r['pitch'], r['length'])
                            wf.write(compose_log(r['ts_origin'], log_type, data))

                    # r = db.decode_message(can_id, buf)
                    # speed = r['CAN_VEHICLE_SPEED'] * 3.6
                    # cols[2] = 'speed'
                    # cols[3] = str(int(speed)) + '\n'
                    # cols = cols[:4]
            wf.write(' '.join(cols))
    wf.close()
    return os.path.abspath('log_rtk.txt')


def parse_drtk_target(file_name):
    from tools.geo import gps_bearing, gps_distance
    print('parsing rtk...')
    ctx = {}
    rtk_pair = [0, 0]
    out_file = 'log_rtk.txt'
    wf = open(out_file, 'w')
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if 'rtk' in cols[2] and 'sol' in cols[2]:
                r = dict()
                r['rtkst'] = int(cols[3])
                r['ts_origin'] = ts
                r['lat'] = float(cols[5])
                r['lon'] = float(cols[6])
                r['hgt'] = float(cols[7])
                r['yaw'] = float(cols[11])
                if cols[2] == 'rtk.2.sol':
                    rtk_pair[0] = [r['ts_origin'], r['lat'], r['lon'], r['hgt'], r['yaw']]
                else:
                    rtk_pair[1] = [r['ts_origin'], r['lat'], r['lon'], r['hgt']]
                if rtk_pair[0] and rtk_pair[1]:
                    if -0.00001 < rtk_pair[0][0] - rtk_pair[1][0] < 0.00001:
                        range = gps_distance(rtk_pair[1][1], rtk_pair[1][2], rtk_pair[0][1],
                                             rtk_pair[0][2])
                        angle = gps_bearing(rtk_pair[1][1], rtk_pair[1][2], rtk_pair[0][1],
                                            rtk_pair[0][2])
                        angle = angle - rtk_pair[0][4]
                        height = rtk_pair[1][3] - rtk_pair[0][3]
                        wf.write(compose_log(r['ts_origin'], 'rtk.target',
                                             '{} {} {}'.format(range, angle, height)))

                    # r = db.decode_message(can_id, buf)
                    # speed = r['CAN_VEHICLE_SPEED'] * 3.6
                    # cols[2] = 'speed'
                    # cols[3] = str(int(speed)) + '\n'
                    # cols = cols[:4]
            wf.write(' '.join(cols))
    wf.close()
    return os.path.abspath(out_file)


def parse_rtk_target_ub482(line, ctx):
    from recorder.convert import ub482_defs, decode_with_def
    from tools.vehicle import Vehicle, get_vehicle_target
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if 'rtk' not in cols[2]:
        return
    if 'rtksol' not in ctx:
        ctx['rtksol'] = {'vehicles': dict(), 'ts': 0}

    _, idx, kw = cols[2].split('.')
    source = 'rtk.{}'.format(idx)
    role = ctx['veh_roles'].get(source)
    # print(ctx['veh_roles'])
    # print('source, role:', source, role)
    if role not in ctx['rtksol']['vehicles']:
        ctx['rtksol']['vehicles'][role] = Vehicle(role)
    r = decode_with_def(ub482_defs, line)
    r['source'] = source
    r['id'] = int(idx)
    if not r:
        return
    lines = ''
    lines += line
    epoch = []
    select = {'bestpos': 'lat', 'bestvel': 'hor_speed', 'heading': 'pitch'}
    key = select.get(r['type'])
    # print(key, r['type'])
    new_epoch = True
    ego_car = ctx['rtksol']['vehicles'].get('ego')
    if not key:
        new_epoch = False
    else:
        for role in ctx['rtksol']['vehicles']:
            # print(ctx['rtksol']['vehicles'])
            if len(ctx['rtksol']['vehicles'][role].dynamics[key]) == 0:
                continue
            if r['ts'] <= ctx['rtksol']['vehicles'][role].dynamics[key][0][0]:
                new_epoch = False
    if new_epoch:
        for role in ctx['rtksol']['vehicles']:
            if role == 'ego':
                continue
            if not ego_car or not ctx['rtksol']['vehicles'][role]:
                continue
            t = get_vehicle_target(ego_car, ctx['rtksol']['vehicles'][role])
            if t:
                epoch.append(t)
    ctx['rtksol']['vehicles'][role].update_dynamics(r)
    # if r['type'] == 'pinpoint':
    #     print(r)


    for t in epoch:
        x, y = ctx['trans'].trans_polar2rcs(t['angle'], t['range'], 'rtk')
        lines += compose_log(ts, 'rtk.target.{}'.format(idx), '{} {} {vel_lon} {TTC}'.format(y, x, **t))

    if not ego_car:
        if epoch:
            ctx['obs_ep']['rtk']['data'] = epoch
            ctx['obs_ep']['rtk']['ts'] = ts
        return

    ppt = ego_car.get_pp_target()
    if ppt:
        # print(ppt)
        ppt['id'] = int(idx)
        x, y = ctx['trans'].trans_polar2rcs(ppt['angle'], ppt['range'], 'rtk')
        epoch.append(ppt)
        lines += compose_log(ts, 'rtk.ppt.{}'.format(idx), '{} {} {vel_lon} {TTC}'.format(y, x,**ppt))
    if epoch:
        ctx['obs_ep']['rtk']['data'] = epoch
        ctx['obs_ep']['rtk']['ts'] = ts

    return lines


def parse_esr_line(line, ctx):
    from parsers.radar import parse_esr
    from math import sin, pi
    can_port = ctx['can_port'].get('esr')
    if can_port is None:
        return
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if not ctx.get('esr_ids'):
        ctx['esr_ids'] = set()
    if can_port in cols[2] or can_port.lower() in cols[2]:
        can_id = int(cols[3], 16)
        buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
        r = parse_esr(can_id, buf, ctx)
        # print(can_port, buf, r)
        if not r or isinstance(r, dict):
            return
        lines = ''

        for item in r:
            # print(type(item), item)
            # print(item['cipo'])
            # if item.get('cipo'):
            # angle_rad = item['angle'] * pi / 180.0
            # x = cos(angle_rad) * item['range']
            # y = sin(angle_rad) * item['range']
            x, y = ctx['trans'].trans_polar2rcs(item['angle'], item['range'], 'esr')

            lines += compose_log(ts, 'esr.obj.{id}'.format(**item),
                                 '{} {} {range_rate} {TTC_m}'.format(y, x, **item))
            ctx['esr_ids'].add(item['id'])
            item['pos_lat'] = y
            item['pos_lon'] = x
        ctx['obs_ep']['esr']['data'] = r
        ctx['obs_ep']['esr']['ts'] = ts
        # ctx['esr_obs_ep'] = r
        # ctx['esr_obs_ep_ts'] = ts
        # print(lines)
        return lines


def parse_ars_line(line, ctx):
    from parsers.radar import parse_ars
    if not ctx.get('ars_ids'):
        ctx['ars_ids'] = set()
    can_port = ctx['can_port'].get('ars')
    if can_port is None:
        return
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000

    if can_port in cols[2] or can_port.lower() in cols[2]:
        can_id = int(cols[3], 16)
        buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
        r = parse_ars(can_id, buf, ctx)
        # print(can_port, buf, r)
        if not r or isinstance(r, dict):
            return
        lines = ''

        for item in r:
            # print(item)
            x, y = ctx['trans'].trans_polar2rcs(item['angle'], item['range'], 'ars')

            lines += compose_log(ts, 'ars.obj.{id}'.format(**item),
                                 '{} {} {vel_lon} {TTC}'.format(y, x, **item))
            ctx['ars_ids'].add(item['id'])
            item['pos_lat'] = y
            item['pos_lon'] = x
        ctx['obs_ep']['ars']['data'] = r
        ctx['obs_ep']['ars']['ts'] = ts
        # ctx['esr_obs_ep'] = r
        # ctx['esr_obs_ep_ts'] = ts
        # print(lines)
        return lines


def parse_lmr_line(line, ctx, can_port='CAN2'):
    from parsers.radar import parse_hawkeye_lmr
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if can_port in cols[2]:
        can_id = int(cols[3], 16)
        buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
        r = parse_hawkeye_lmr(can_id, buf, ctx)
        # print(can_port, buf, r)
        if not r:
            return
        return compose_log(ts, 'lmr.obj.{}'.format(r['id']), '{} {}'.format(r['range'], r['angle']))


def parse_x1_line(line, ctx):
    can_port = ctx['can_port'].get('x1')
    if can_port is None:
        return
    if not ctx.get('x1_ids'):
        ctx['x1_ids'] = set()
    if not ctx.get('x1_fusion_ids'):
        ctx['x1_fusion_ids'] = set()
    from parsers.x1 import parse_x1
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if can_port in cols[2] or can_port.lower() in cols[2]:
        can_id = int(cols[3], 16)
        buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
        ret = parse_x1(can_id, buf, ctx)
        # print(ret)
        speed = ctx.get('speed') or 0
        # print(can_port, buf, r)
        if not ret or not isinstance(ret, list):
            return
        # print(ret)
        lines = ''
        obs_type = 'x1'
        for r in ret:
            # print(r)
            if r['type'] != 'obstacle':
                return
            if 'no vehicle' in r['class']:
                continue
            obs_type = r['sensor']
            if r['sensor'] == 'x1':
                # print(r)
                x, y = ctx['trans'].compensate_param_rcs(r['pos_lon'], r['pos_lat'], 'x1')
                lines += compose_log(ts, 'x1.{class}.{id}'.format(**r),
                                     '{} {} {} {}'.format(y, x, (r['vel_lon']), r.get('TTC') or 7.0))
                ctx['x1_ids'].add(r['id'])
            elif r['sensor'] == 'x1_fusion':
                x, y = ctx['trans'].compensate_param_rcs(r['pos_lon'], r['pos_lat'], 'x1')
                lines += compose_log(ts, 'x1_fusion.{class}.{id}'.format(**r),
                                     '{} {} {} {}'.format(y, x, (r['vel_lon']), r.get('TTC') or 7.0))
                ctx['x1_fusion_ids'].add(r['id'])
            else:
                return
        ctx['obs_ep'][obs_type]['data'] = ret
        ctx['obs_ep'][obs_type]['ts'] = ts
        # print(len(ctx['obs_ep']['x1']['data']))
        return lines


# deprecated
def parse_x1_fusion_line(line, ctx):
    can_port = ctx['can_port'].get('x1')
    if can_port is None:
        return
    if not ctx.get('x1_ids'):
        ctx['x1_ids'] = set()
    from parsers.x1 import parse_x1
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if can_port in cols[2] or can_port.lower() in cols[2]:
        can_id = int(cols[3], 16)
        buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
        ret = parse_x1(can_id, buf, ctx)
        # print(ret)
        speed = ctx.get('speed') or 0
        # print(can_port, buf, r)
        if not ret or not isinstance(ret, list):
            return
        # print(ret)
        lines = ''

        # ctx['x1_obs_ep'] = ret
        # ctx['x1_obs_ep_ts'] = ts

        for r in ret:
            if r['type'] != 'obstacle':
                return
            # print(r)
            if 'no vehicle' in r['class']:
                continue
            if r['sensor'] != 'x1_fusion':
                return

            x, y = ctx['trans'].compensate_param_rcs(r['pos_lon'], r['pos_lat'], 'x1')
            lines += compose_log(ts, 'x1_fusion.{class}.{id}'.format(**r),
                                 '{} {} {} {}'.format(y, x, (r['vel_lon']), r.get('TTC') or 7.0))
            ctx['x1_ids'].add(r['id'])
        ctx['obs_ep']['x1']['data'] = ret
        ctx['obs_ep']['x1']['ts'] = ts
        return lines


def parse_q3_line(line, ctx):
    from parsers.mobileye_q3 import parse_ifv300
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    can_port = ctx['can_port'].get('ifv300')
    if can_port is None:
        return
    if can_port in cols[2] or can_port.lower() in cols[2]:
        can_id = int(cols[3], 16)
        buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
        ret = parse_ifv300(can_id, buf, ctx)
        # print(can_port, buf, r)

        if not ret:
            return
        # print(ret)
        if 'type' in ret and ret['type'] == 'vehicle_state':
            # print(ret['speed'])
            ctx['q3_speed'] = ret['speed']/3.6
        if isinstance(ret, list):
            lines = ''
            if 'q3_ids' not in ctx:
                ctx['q3_ids'] = set()
            for r in ret:
                if r['type'] != 'obstacle':
                    return
                # print('0x{:x}'.format(r['id']), ts)
                # print(r)
                speed = ctx.get('q3_speed') or 0
                x, y = ctx['trans'].compensate_param_rcs(r['pos_lon'], r['pos_lat'], 'ifv300')
                lines += compose_log(ts, 'q3.{class}.{id}'.format(**r),
                                     '{} {} {} {}'.format(y, x, r['vel_lon'] - speed, r['TTC']))
            # ctx['q3_obs_ep'] = ret
            # ctx['q3_obs_ep_ts'] = ts
                ctx['q3_ids'].add(r['id'])
            ctx['obs_ep']['q3']['data'] = ret
            ctx['obs_ep']['q3']['ts'] = ts
            return lines
        else:
            if ret['type'] not in ['obstacle', 'vehicle_state', 'obstacle_f']:
                return
            if ret['type'] == 'vehicle_state':
                return compose_log(ts, 'q3.vehstate', '{} {}'.format(ret['speed'], ret['yaw_rate']))
            # return compose_log(ts, 'q3.{}.{}'.format(ret['class'], ret['id']),
            #                    '{} {}'.format(ret['pos_lat'], ret['pos_lon']))


def parse_nmea_line(line, ctx):
    from parsers.ublox import parse_ublox
    cols = line.split(' ')
    if cols[2] == 'NMEA' or 'gps' in cols[2]:
        r = parse_ublox('NMEA', cols[3])
        if r and 'speed' in r:
            if 'speed' not in ctx:
                ctx['speed'] = {}
            ts = float(cols[0]) + float(cols[1]) / 1000000
            ctx['speed']['gps'] = {'ts': ts, 'speed': r['speed']}


def parse_x1l_line(line, ctx):
    from parsers.x1l import parse_x1l
    cols = line.split()
    can_port = ctx['can_port'].get('x1l')
    if cols[2] == can_port:
        ts = float(cols[0]) + float(cols[1]) / 1000000
        can_id = int(cols[3], 16)
        buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
        r = parse_x1l(can_id, buf, ctx)
        if r is not None:
            x = r['pos_lon']
            y = 0
            speed = 0
            line = compose_log(ts, 'x1l.{class}.{id}'.format(**r), '{} {} {} {}'.format(y, x, speed, r['TTC']))


def trans_line_to_asc(line, ctx):
    cols = line.split(' ')
    
    if cols[2][:3] == 'CAN':
        lines = ''
        time_init = ctx.get('asc_t0')
        if not time_init:
            ctx['asc_t0'] = float(cols[0] + '.' + cols[1])
            time_init = ctx['asc_t0']
        new_time = float(cols[0] + '.' + cols[1]) - time_init
        lines += str(new_time)
        lines += ' '
        lines += str(int(cols[2][3]) + 1)
        lines += ' '
        if len(cols[3]) > 6:
            lines += cols[3][2:]
            lines += 'x'
        else:
            lines += cols[3][2:]

        lines += ' Rx d 8 '
        lines += ' '.join(cols[4:])
        lines += '\n'
        return lines


def parse_d530_line(line, ctx):
    from parsers.df_d530 import parse_dfd530
    cols = line.split(' ')
    can_port = ctx['can_port'].get('d530')
    if cols[2] == can_port:
        ts = float(cols[0]) + float(cols[1]) / 1000000
        can_id = int(cols[3], 16)
        buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
        r = parse_dfd530(can_id, buf, ctx)
        if not r:
            return
        lines = ''
        if 'd530' not in ctx:
            ctx['d530'] = {'aeb_level': 0, 'xbr_acc': 0}
        x1_data = None
        x1f_data = None
        ars_data = None
        if ctx['obs_ep']['x1'].get('data'):
            for x1_obs in ctx['obs_ep']['x1'].get('data'):
                if x1_obs.get('cipo'):
                    x1_data = x1_obs
                    break
        if ctx['obs_ep']['x1_fusion'].get('data'):
            # print('x1 fusion has data', len(ctx['obs_ep']['x1_fusion'].get('data')))
            for x1f_obs in ctx['obs_ep']['x1_fusion'].get('data'):
                if x1f_obs.get('cipo'):
                    x1f_data = x1f_obs
                    break
        if ctx['obs_ep']['ars'].get('data'):
            for ars_obs in ctx['obs_ep']['ars'].get('data'):
                if ars_obs.get('cipo'):
                    ars_data = ars_obs
                    break
        if 'aeb_level' in r:
            data = r['aeb_level']
            lines += compose_log(ts, 'd530.{}'.format(r['class']), '{}'.format(data))

            if ctx['d530']['aeb_level'] == 0 and data == 1:
                ctx['d530']['fcw1'] = {'ts': ts, 'speed': ctx['speed'], 'x1': x1_data, 'x1f': x1f_data, 'ars': ars_data}

                lines += compose_log(ts, 'd530.aebw0to1', '{}'.format(data))

            elif ctx['d530']['aeb_level'] == 1 and data == 2:
                ctx['d530']['fcw2'] = {'ts': ts, 'speed': ctx['speed'], 'x1': x1_data, 'x1f': x1f_data, 'ars': ars_data}
                lines += compose_log(ts, 'd530.aebw1to2', '{}'.format(data))

        elif 'xbr_acc' in r:
            data = r['xbr_acc']
            lines += compose_log(ts, 'd530.{}'.format(r['class']), '{}'.format(data))
            if data < -5.0 and ctx['d530']['xbr_acc'] > -1.0:
                ctx['d530']['aeb'] = {'ts': ts, 'speed': ctx['speed'], 'x1': x1_data, 'x1f': x1f_data, 'ars': ars_data}
                lines += compose_log(ts, 'd530.xbrtrigger', '{}'.format(data))
        elif 'speed' in r:
            if 'speed' not in ctx:
                ctx['speed'] = {}
            ctx['speed']['d530'] = {'ts': ts, 'speed': r['speed']}
        ctx['d530'].update(r)


def adj_timestamp(line, ctx, log_type='NMEA'):
    cols = line.split(' ')
    if cols[2] != log_type:
        tv_s = int(cols[0])
        tv_us = int(cols[1])
        ts = tv_s * 1000000 + tv_us
        ctx['last_tick'] = ts
        return

    last_tick = ctx.get('last_tick')

    if last_tick:
        cols[0] = str(int(last_tick / 1000000))
        cols[1] = '%.6d' % (last_tick % 1000000)
        return ' '.join(cols) + '\n'


def merge_log(log1, log2, outfile=None):
    out = outfile or '/tmp/log_merged.txt'
    out_cat = '/tmp/log_cat.txt'
    with open(out_cat, 'w') as wf:
        with open(log1) as f1, open(log2) as f2:
            wf.write(f1.read())
            wf.write(f2.read())
    return time_sort(out_cat, output=out)


# def find_esr_by_x1(line, ctx):
#     cols = line.split(' ')
#     ts = float(cols[0]) + float(cols[1]) / 1000000
#     if 'x1.' in cols[2]:
#         pass

def trans_to_hil(log, output=None):
    from tools.log_info import get_connected_sensors, get_main_index
    from parsers import ublox, parser
    data_dir = os.path.dirname(log)
    if not os.path.exists(data_dir):
        print('no such dir')
        return None

    print('processing', data_dir)
    video_files = sorted(os.listdir(os.path.join(data_dir, 'video')))
    print(video_files)
    if not video_files:
        print('video files not found!')
        return
    midx = get_main_index(log)
    connected = get_connected_sensors(log)
    if midx is None:
        imu = 'Gsensor'
    else:
        imu = 'Gsensor.{}'.format(midx)
        if imu not in connected:
            for idx in range(10):
                imu_aux = 'Gsensor.{}'.format(idx)
                if imu_aux in connected:
                    imu = imu_aux
                    break

    print('use {} as imu.'.format(imu))

    speed_meter = None
    kw = None
    ctx = {}

    for sensor in ['mqb', 'bestvel', 'gps', 'ifv300']:
        for port in connected:
            if sensor == connected[port]:
                speed_meter = port
                kw = sensor
                break
        if kw:
            break
    if speed_meter is None:
        print('sensor for speed not found. please check the data.')
        return
    elif 'bestvel' == kw:
        def spd_parser(cols):
            return float(cols[7]) * 3.6
    elif 'gps' == kw:
        def spd_parser(cols):
            r = ublox.decode_nmea(cols[3])
            if r and r.get('speed') is not None:
                return r['speed']
    elif kw in parser.parsers_dict:
        def spd_parser(cols):
            data = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
            can_id = int(cols[3], 16)
            can_parser = parser.parsers_dict.get(kw)
            r = can_parser(can_id, data, ctx)
            if r and 'speed' in r:
                return r['speed']
    else:
        def spd_parser(cols):
            return None
    print('use {} as speed meter.'.format(speed_meter))
    # os.rename(os.path.join(data_dir, 'log.txt'), os.path.join(data_dir, 'log0.txt'))
    if output:
        parser_hil = open(os.path.join(output, 'log_for_hil.txt'), 'w')
    else:
        parser_hil = open(os.path.join(data_dir, 'log_for_hil.txt'), 'w')
    lines = []

    # for video_file in video_files:
    #     os.rename(os.path.join(data_dir, 'video', video_file), os.path.join(data_dir, video_file))
    video_files.append("")  # 追加一个空元素，否则如果最后一个视频刚好1200帧，会报错

    # read speed from rtk data
    with open(log) as can_log:
        cnt_cam = 0
        cnt_video = 0
        video_name = video_files[cnt_video]
        for line in can_log:
            line = line.strip()
            if not line:
                continue
            cols = line.split()
            if cols[2] == speed_meter:
                speed = spd_parser(cols)
                if speed is not None:
                    row = cols[0], cols[1], 'speed', '%.6f' % speed
                    lines.append(' '.join(row))
            # if cols[2].startswith('rtk') and cols[2].endswith('bestvel'):
            #     speed = float(cols[7]) * 3.6
            #     row = cols[0], cols[1], 'speed', '%.6f' % speed
            #     # print(' '.join(row), file=parser_hil)
            #     lines.append(' '.join(row))
            elif cols[2].startswith('CAN'):
                lines.append(line)
            elif cols[2] == 'camera':
                ts = int(cols[0])
                vs = int(cols[1])
                s = " ".join(['%010d' % ts, '%06d' % vs, 'cam_frame', 'video/'+video_name, str(cnt_cam)])
                lines.append(s)
                cnt_cam += 1
                if cnt_cam >= 1200:
                    cnt_video += 1
                    cnt_cam = 0
                    video_name = video_files[cnt_video]
            elif cols[2] == imu:
                # print(imu)
                cols[2] = 'Gsensor'
                s = ' '.join(cols)
                lines.append(s)

    cnt_frames = cnt_video * 1200 + cnt_cam
    print(cnt_frames, ' video frames')
    print(len(lines) - cnt_frames, 'speed and CAN lines')
    # lines.sort()
    for line in lines:
        print(line, file=parser_hil)
    parser_hil.close()


def get_distance(t1, t2):
    if 'pos_lat' not in t1:
        # t1x, t1y = trans_polar2rcs(t1['angle'], t1['range'])
        t1x = cos(t1['angle'] * pi / 180.0) * t1['range']
        t1y = sin(t1['angle'] * pi / 180.0) * t1['range']
    else:
        t1y = t1['pos_lat']
        t1x = t1['pos_lon']
    if 'pos_lat' not in t2:
        # t2x, t2y = trans_polar2rcs(t2['angle'], t2['range'])
        t2x = cos(t2['angle'] * pi / 180.0) * t2['range']
        t2y = sin(t2['angle'] * pi / 180.0) * t2['range']
    else:
        t2y = t2['pos_lat']
        t2x = t2['pos_lon']

    dist = ((t1x - t2x) ** 2 + (t1y - t2y) ** 2) ** 0.5
    return dist


def spatial_match_obs(obs1, obs2):
    obs2_cdt = dict()
    for obs1item in obs1:
        if len(obs2) > 0:
            obs2list = sorted(obs2, key=lambda x: get_distance(obs1item, x))
            obs2t = obs2list[0]

            x = obs1item.get('range') or obs1item['pos_lon']
            dx = get_distance(obs1item, obs2t)
            if x > 60 and dx / x > 0.1:
                continue
            elif dx > 6.0:
                # print('dist too large.', x1item['id'], esr_t['id'], get_distance(x1item, esr_t))
                continue
            if obs2t['id'] not in obs2_cdt:
                obs2_cdt[obs2t['id']] = dict()
            obs2_cdt[obs2t['id']][obs1item['id']] = {'dist': get_distance(obs1item, obs2t)}

    # print(obs2_cdt)
    ret = list()
    for o2id in obs2_cdt:
        # print(eid)
        dist = 99
        o1sel = 0
        # if o2id == 7:
        #     print(obs2_cdt[o2id])
        for o1id in obs2_cdt[o2id]:
            if obs2_cdt[o2id][o1id]['dist'] < dist:
                dist = obs2_cdt[o2id][o1id]['dist']
                o1sel = o1id
        # ts = x1_ts
        # pair = {'x1': o1sel, 'esr': o2id}
        for o1 in obs1:
            for o2 in obs2:
                if o1['id'] == o1sel and o2['id'] == o2id:
                    yield (o1, o2)


def match_x1_esr(line, ctx):
    if 'x1' not in ctx['obs_ep'] or 'esr' not in ctx['obs_ep']:
        return
    if not ctx.get('matched_ep'):
        ctx['matched_ep'] = dict()
    if ctx['obs_ep']['esr'].get('ts') == ctx['obs_ep']['esr'].get('ts_last') and \
            ctx['obs_ep']['x1'].get('ts') == ctx['obs_ep']['x1'].get('ts_last'):
        return

    # print(ctx['obs_ep']['esr'].keys())
    if ctx['obs_ep']['esr'].get('ts') != ctx['obs_ep']['esr'].get('ts_last'):
        # if 'buff' not in ctx:
        #     ctx['esr_buff'] = deque(maxlen=10)
        esr = ctx['obs_ep']['esr'].get('data')
        ctx['obs_ep']['esr']['buff'].append((ctx['obs_ep']['esr']['ts'], esr))
        ctx['obs_ep']['esr']['ts_last'] = ctx['obs_ep']['esr']['ts']

    if ctx['obs_ep']['x1'].get('ts') != ctx['obs_ep']['x1'].get('ts_last'):
        # if 'x1_buff' not in ctx:
        #     ctx['x1_buff'] = deque(maxlen=10)
        x1 = ctx['obs_ep']['x1'].get('data')
        ctx['obs_ep']['x1']['buff'].append((ctx['obs_ep']['x1']['ts'], x1))
        ctx['obs_ep']['x1']['ts_last'] = ctx['obs_ep']['x1']['ts']

    done = False
    for i in range(len(ctx['obs_ep']['x1']['buff']) - 1, 0, -1):
        for j in range(len(ctx['obs_ep']['esr']['buff']) - 1, 0, -1):
            ts = ctx['obs_ep']['x1']['buff'][i][0]
            ts0 = ctx['obs_ep']['esr']['buff'][j-1][0]
            ts1 = ctx['obs_ep']['esr']['buff'][j][0]

            if ts0 < ts <= ts1:
                x1_obs_t = ctx['obs_ep']['x1']['buff'][i][1]
                # print(len(ctx['x1_buff'][i][1]), len(ctx['esr_buff'][j][1]))
                if ts - ts0 > ts1 - ts:
                    dt = ts1 - ts
                    esr_obs_t = ctx['obs_ep']['esr']['buff'][j][1]
                else:
                    dt = ts - ts0
                    esr_obs_t = ctx['obs_ep']['esr']['buff'][j-1][1]

                if dt > 0.1:
                    done = True
                    break
                # ret = spatial_match_obs(x1_obs_t, esr_obs_t)
                # if not ret:
                #     done = True
                    # print('no spatial match', len(x1_obs_t), len(esr_obs_t), ts - ts0, ts1 - ts)
                    # break
                for ret in spatial_match_obs(x1_obs_t, esr_obs_t):
                    x1sel, esrsel = ret
                    pair = {'x1': x1sel, 'esr': esrsel}
                    # ctx['matched_ep'][ts] = pair
                    if ts not in ctx['matched_ep']:
                        ctx['matched_ep'][ts] = list()
                    ctx['matched_ep'][ts].append(pair)
                done = True
                break
        if done:
            break
    # x1_dt = ctx['x1_obs_ep_ts'] - ctx['x1_obs_ep_ts_last'] if 'x1_obs_ep_ts_last' in ctx else None
    # esr_dt = ctx['esr_obs_ep_ts'] - ctx['esr_obs_ep_ts_last'] if 'esr_obs_ep_ts_last' in ctx else None
    # print(ctx['x1_obs_ep_ts'], 'x1 dt:', x1_dt, 'esr dt:', esr_dt)
    # print('ok')


def _match_obs(names, ctx):
    key0, key1 = names
    done = False
    # print(key0, len(ctx['obs_ep'][key0]['buff']), key1, len(ctx['obs_ep'][key1]['buff']))
    for i in range(len(ctx['obs_ep'][key0]['buff']) - 1, 0, -1):
        ts = ctx['obs_ep'][key0]['buff'][i][0]
        for j in range(len(ctx['obs_ep'][key1]['buff']) - 1, 0, -1):
            ts0 = ctx['obs_ep'][key1]['buff'][j - 1][0]
            ts1 = ctx['obs_ep'][key1]['buff'][j][0]

            if ts0 < ts <= ts1:
                k0_obs_t = ctx['obs_ep'][key0]['buff'][i][1]
                # print(k0_obs_t)
                # print(len(ctx['x1_buff'][i][1]), len(ctx['q3_buff'][j][1]))
                if ts - ts0 > ts1 - ts:
                    dt = ts1 - ts
                    k1_obs_t = ctx['obs_ep'][key1]['buff'][j][1]
                else:
                    dt = ts - ts0
                    k1_obs_t = ctx['obs_ep'][key1]['buff'][j - 1][1]

                if dt > 0.1:
                    done = True
                    break
                # ret = spatial_match_obs(x1_obs_t, k1_obs_t)
                # if not ret:
                #     done = True
                # print('no spatial match', len(x1_obs_t), len(k1_obs_t), ts - ts0, ts1 - ts)
                # break
                # print(k1_obs_t)
                for ret in spatial_match_obs(k0_obs_t, k1_obs_t):
                    k0sel, k1sel = ret
                    candidate = {key1: {'id': k1sel['id'], 'dist': get_distance(k0sel, k1sel)}}
                    # ctx['matched_ep'][ts] = pair
                    if ts not in ctx['matched_ep']:
                        ctx['matched_ep'][ts] = dict()
                    # found = False
                    if k0sel['id'] not in ctx['matched_ep'][ts]:
                        ctx['matched_ep'][ts][k0sel['id']] = dict()
                    ctx['matched_ep'][ts][k0sel['id']].update(candidate)
                    # if not found:
                    #     ctx['matched_ep'][ts].append(pair)
                    # print(ctx['matched_ep'][ts])
                    done = True
        if done:
            break


def match_obs(line, ctx):
    if len(ctx['obs_ep']) < 2:  # at least 2 obs are updated
        return
    if not ctx.get('matched_ep'):
        # print('matched ep')
        ctx['matched_ep'] = dict()

    updated = False

    for obs_type in ctx['sensors']:
        if obs_type not in ctx['obs_ep']:
            continue
        if ctx['obs_ep'][obs_type].get('ts') != ctx['obs_ep'][obs_type].get('ts_last'):
            if 'buff' not in ctx['obs_ep'][obs_type]:
                ctx['obs_ep'][obs_type]['buff'] = deque(maxlen=10)
            data = ctx['obs_ep'][obs_type]['data']
            ctx['obs_ep'][obs_type]['buff'].append((ctx['obs_ep'][obs_type]['ts'], data))
            ctx['obs_ep'][obs_type]['ts_last'] = ctx['obs_ep'][obs_type]['ts']
            updated = True

    # if ctx.get('x1_obs_ep_ts') != ctx.get('x1_obs_ep_ts_last'):
    #     if 'x1_buff' not in ctx:
    #         ctx['x1_buff'] = deque(maxlen=10)
    #     x1 = ctx.get('x1_obs_ep')
    #     ctx['x1_buff'].append((ctx['x1_obs_ep_ts'], x1))
    #     ctx['x1_obs_ep_ts_last'] = ctx['x1_obs_ep_ts']
    #     updated = True

    if not updated:
        return
    # print(ctx['obs_ep']['q3'])
    for sensor in ctx['sensors']:
        if sensor == 'x1':
            continue
        _match_obs(('x1', sensor), ctx)
    # _match_obs(('x1', 'esr'), ctx)
    # _match_obs(('x1', 'q3'), ctx)
    # _match_obs(('x1', 'rtk'), ctx)
    # done = False
    # for i in range(len(ctx['obs_ep']['x1']['buff']) - 1, 0, -1):
    #     ts = ctx['obs_ep']['x1']['buff'][i][0]
    #     for j in range(len(ctx['obs_ep']['esr']['buff']) - 1, 0, -1):
    #
    #         ts0 = ctx['obs_ep']['esr']['buff'][j-1][0]
    #         ts1 = ctx['obs_ep']['esr']['buff'][j][0]
    #
    #         if ts0 < ts <= ts1:
    #             x1_obs_t = ctx['obs_ep']['x1']['buff'][i][1]
    #             # print(len(ctx['x1_buff'][i][1]), len(ctx['esr_buff'][j][1]))
    #             if ts - ts0 > ts1 - ts:
    #                 dt = ts1 - ts
    #                 esr_obs_t = ctx['obs_ep']['esr']['buff'][j][1]
    #             else:
    #                 dt = ts - ts0
    #                 esr_obs_t = ctx['obs_ep']['esr']['buff'][j-1][1]
    #
    #             if dt > 0.1:
    #                 done = True
    #                 break
    #             # ret = spatial_match_obs(x1_obs_t, esr_obs_t)
    #             # if not ret:
    #             #     done = True
    #                 # print('no spatial match', len(x1_obs_t), len(esr_obs_t), ts - ts0, ts1 - ts)
    #                 # break
    #             for ret in spatial_match_obs(x1_obs_t, esr_obs_t):
    #                 x1sel, esrsel = ret
    #                 candidate = {'esr': {'id': esrsel['id'], 'dist': get_distance(x1sel, esrsel)}}
    #                 # ctx['matched_ep'][ts] = pair
    #                 # print(candidate)
    #                 if ts not in ctx['matched_ep']:
    #                     ctx['matched_ep'][ts] = dict()
    #                 if x1sel['id'] not in ctx['matched_ep'][ts]:
    #                     ctx['matched_ep'][ts][x1sel['id']] = dict()
    #                 ctx['matched_ep'][ts][x1sel['id']].update(candidate)
    #                 # print(ctx['matched_ep'][ts])
    #                 done = True
    #             break
    #
    # for i in range(len(ctx['obs_ep']['x1']['buff']) - 1, 0, -1):
    #     ts = ctx['obs_ep']['x1']['buff'][i][0]
    #     for j in range(len(ctx['obs_ep']['q3']['buff']) - 1, 0, -1):
    #         ts0 = ctx['obs_ep']['q3']['buff'][j - 1][0]
    #         ts1 = ctx['obs_ep']['q3']['buff'][j][0]
    #
    #         if ts0 < ts <= ts1:
    #             x1_obs_t = ctx['obs_ep']['x1']['buff'][i][1]
    #             # print(len(ctx['x1_buff'][i][1]), len(ctx['q3_buff'][j][1]))
    #             if ts - ts0 > ts1 - ts:
    #                 dt = ts1 - ts
    #                 q3_obs_t = ctx['obs_ep']['q3']['buff'][j][1]
    #             else:
    #                 dt = ts - ts0
    #                 q3_obs_t = ctx['obs_ep']['q3']['buff'][j - 1][1]
    #
    #             if dt > 0.1:
    #                 done = True
    #                 break
    #             # ret = spatial_match_obs(x1_obs_t, q3_obs_t)
    #             # if not ret:
    #             #     done = True
    #             # print('no spatial match', len(x1_obs_t), len(q3_obs_t), ts - ts0, ts1 - ts)
    #             # break
    #             for ret in spatial_match_obs(x1_obs_t, q3_obs_t):
    #                 x1sel, q3sel = ret
    #                 candidate = {'q3': {'id': q3sel['id'], 'dist':get_distance(x1sel, q3sel)}}
    #                 # ctx['matched_ep'][ts] = pair
    #                 if ts not in ctx['matched_ep']:
    #                     ctx['matched_ep'][ts] = dict()
    #                 # found = False
    #                 if x1sel['id'] not in ctx['matched_ep'][ts]:
    #                     ctx['matched_ep'][ts][x1sel['id']] = dict()
    #                 ctx['matched_ep'][ts][x1sel['id']].update(candidate)
    #                 # if not found:
    #                 #     ctx['matched_ep'][ts].append(pair)
    #                 # print(ctx['matched_ep'][ts])
    #                 done = True
    #             # break
    #     if done:
    #         break

# deprecated
# def pair_x1_esr(line, ctx):
#     from tools.match import is_near
#     cols = line.split(' ')
#     ts = float(cols[0]) + float(cols[1]) / 1000000
#     id = int(cols[2].split('.')[-1])
#     if not ctx.get('matched'):
#         ctx['matched'] = dict()
#         # ctx['matched']['x1'] = set()
#         # ctx['matched']['esr'] = set()
#     # print(line)
#     if 'x1.' in cols[2]:
#         if ctx.get('x1_target') and id not in ctx['x1_target']:
#             return
#
#         y = float(cols[3])
#         x = float(cols[4])
#         vlon_rel = float(cols[5])
#         # ttc = float(cols[6])
#         # range_rate =
#         ctx['x1_obj'] = {'ts': ts, 'id': id, 'pos_lat': y, 'pos_lon': x, 'vel_lon': vlon_rel}
#     elif 'esr.' in cols[2]:
#         if ctx.get('radar_target') and id not in ctx['radar_target']:
#             return
#
#         r = float(cols[3])
#         a = float(cols[4])
#         range_rate = float(cols[5])
#         y = float(cols[6])
#         ctx['esr_obj'] = {'ts': ts, 'id': id, 'range': r, 'angle': a, 'range_rate': range_rate, 'pos_lat': y}
#     else:
#         return
#
#     if 'x1_obj' in ctx and 'esr_obj' in ctx:
#         # print(ctx['x1_obj'], ctx['esr_obj'])
#         if fabs(ctx['x1_obj']['ts'] - ctx['esr_obj']['ts']) < 0.2:
#             if not is_near(ctx['x1_obj'], ctx['esr_obj']):
#                 # print('not matched.', ctx['x1_obj']['id'], ctx['esr_obj']['id'])
#                 return
#             # print('matched.', ctx['x1_obj']['id'], ctx['esr_obj']['id'])
#             x1_id = ctx['x1_obj']['id']
#             esr_id = ctx['esr_obj']['id']
#             if x1_id not in ctx['matched']:
#                 ctx['matched'][x1_id] = list()
#             ctx['matched'][x1_id].append(esr_id)
#             # ctx['matched']['esr'].add(ctx['esr_obj']['id'])
#             if not ctx.get('dx'):
#                 ctx['dx'] = []
#             if not ctx.get('dy'):
#                 ctx['dy'] = []
#             if not ctx.get('dvx'):
#                 ctx['dvx'] = []
#             if not ctx.get('pct_dx'):
#                 ctx['pct_dx'] = []
#             if not ctx.get('pct_dy'):
#                 ctx['pct_dy'] = []
#             if not ctx.get('pct_dvx'):
#                 ctx['pct_dvx'] = []
#             # print('matched.', ctx['x1_obj'], ctx['esr_obj'])
#             dx = ctx['x1_obj']['pos_lon'] - ctx['esr_obj']['range']
#             dx_ratio = fabs(dx / ctx['esr_obj']['range']) if ctx['esr_obj']['range'] != 0 else 0
#             dy = ctx['x1_obj']['pos_lat'] - ctx['esr_obj']['pos_lat']
#             dy_ratio = fabs(dy / ctx['esr_obj']['pos_lat']) if ctx['esr_obj']['pos_lat'] != 0 else 0
#             dvx = ctx['x1_obj']['vel_lon'] - ctx['esr_obj']['range_rate']
#             dvx_ratio = fabs(dvx / ctx['esr_obj']['range_rate']) if ctx['esr_obj']['range_rate'] != 0 else 0
#             ctx['dx'].append(dx)
#             ctx['dy'].append(dy)
#             ctx['dvx'].append(dvx)
#             ctx['pct_dx'].append(dx_ratio * 100)
#             ctx['pct_dy'].append(dy_ratio * 100)
#             ctx['pct_dvx'].append(dvx_ratio * 100)
#             ctx['end_ts'] = ts
#             if not ctx.get('start_ts'):
#                 ctx['start_ts'] = ts
#             return compose_log(ts, 'match.x1_esr.{}.{}'.format(x1_id, esr_id), '{} {} {} {} {} {}'.format(
#                 dx, dy, dvx, dx_ratio, dy_ratio, dvx_ratio))
#         else:
#             pass
#             # print('time diff too large', ctx['x1_obj']['ts'], ctx['esr_obj']['ts'])


def calc_delta_x1_esr_1(matched_ep, out_dir):
    diff = os.path.join(out_dir, 'log_diff.txt')
    with open(diff, 'w') as of:
        for ts in sorted(matched_ep):
            for pair in matched_ep[ts]:
                obs1 = pair[0]
                obs2 = pair[1]
                dx = obs1['pos_lon'] - obs2['pos_lon']
                dy = obs1['pos_lat'] - obs2['pos_lat']
                vx1 = obs1['vel_lon'] if 'vel_lon' in obs1 else obs1['range_rate']
                vx2 = obs2['vel_lon'] if 'vel_lon' in obs2 else obs2['range_rate']
                dvx = vx1 - vx2

                dx_ratio = fabs(dx / obs2['pos_lon']) if obs2['pos_lon'] != 0 else 1
                dy_ratio = fabs(dy / obs2['pos_lat']) if obs2['pos_lat'] != 0 else 1
                dvx_ratio = fabs(dvx / vx2) if vx2 != 0 else 1

                line = compose_log(ts, 'match.{}_{}.{}.{}'.format(obs1['sensor'], obs2['sensor'], obs1['id'], obs2['id']), '{} {} {} {} {} {}'.format(
                    dx, dy, dvx, dx_ratio * 100, dy_ratio * 100, dvx_ratio * 100))
                of.write(line)

    return diff


def calc_delta_x1_esr(line, ctx):
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if 'x1.' in cols[2]:
        id = int(cols[2].split('.')[-1])
        if id not in ctx['match_tree']:
            return

        y = float(cols[3])
        x = float(cols[4])
        vlon_rel = float(cols[5])
        # ttc = float(cols[6])
        # range_rate =
        ctx['x1_obj'] = {'ts': ts, 'id': id, 'pos_lat': y, 'pos_lon': x, 'vel_lon': vlon_rel}
    elif 'esr.' in cols[2]:
        id = int(cols[2].split('.')[-1])
        find = False
        for x in ctx['match_tree']:
            if id in ctx['match_tree'][x]:
                find = True
                break
        if not find:
            return

        r = float(cols[3])
        a = float(cols[4])
        range_rate = float(cols[5])
        y = float(cols[6])
        ctx['esr_obj'] = {'ts': ts, 'id': id, 'range': r, 'angle': a, 'range_rate': range_rate, 'pos_lat': y}
    else:
        return

    if 'x1_obj' in ctx and 'esr_obj' in ctx:
        x1_id = ctx['x1_obj']['id']
        esr_id = ctx['esr_obj']['id']
        if esr_id not in ctx['match_tree'][x1_id]:
            return
        if ctx['match_tree'][x1_id][esr_id]['count'] <= 1:
            return
        if ts > ctx['match_tree'][x1_id][esr_id]['end_ts']:
            return
        if ts < ctx['match_tree'][x1_id][esr_id]['start_ts']:
            return
        # print(ctx['x1_obj'], ctx['esr_obj'])
        if fabs(ctx['x1_obj']['ts'] - ctx['esr_obj']['ts']) < 100:

            # if x1_id not in ctx['matched']:
            #     ctx['matched'][x1_id] = list()
            # ctx['matched'][x1_id].append(esr_id)
            # ctx['matched']['esr'].add(ctx['esr_obj']['id'])
            if not ctx.get('dx'):
                ctx['dx'] = []
            if not ctx.get('dy'):
                ctx['dy'] = []
            if not ctx.get('dvx'):
                ctx['dvx'] = []
            if not ctx.get('pct_dx'):
                ctx['pct_dx'] = []
            if not ctx.get('pct_dy'):
                ctx['pct_dy'] = []
            if not ctx.get('pct_dvx'):
                ctx['pct_dvx'] = []
            # print('matched.', ctx['x1_obj'], ctx['esr_obj'])
            dx = ctx['x1_obj']['pos_lon'] - ctx['esr_obj']['range']
            dx_ratio = fabs(dx / ctx['esr_obj']['range']) if ctx['esr_obj']['range'] != 0 else 0
            dy = ctx['x1_obj']['pos_lat'] - ctx['esr_obj']['pos_lat']
            dy_ratio = fabs(dy / ctx['esr_obj']['pos_lat']) if ctx['esr_obj']['pos_lat'] != 0 else 0
            dvx = ctx['x1_obj']['vel_lon'] - ctx['esr_obj']['range_rate']
            dvx_ratio = fabs(dvx / ctx['esr_obj']['range_rate']) if ctx['esr_obj']['range_rate'] != 0 else 0
            ctx['dx'].append(dx)
            ctx['dy'].append(dy)
            ctx['dvx'].append(dvx)
            ctx['pct_dx'].append(dx_ratio * 100)
            ctx['pct_dy'].append(dy_ratio * 100)
            ctx['pct_dvx'].append(dvx_ratio * 100)
            ctx['end_ts'] = ts
            if not ctx.get('start_ts'):
                ctx['start_ts'] = ts
            return compose_log(ts, 'match.x1_esr.{}.{}'.format(x1_id, esr_id), '{} {} {} {} {} {}'.format(
                dx, dy, dvx, dx_ratio * 100, dy_ratio * 100, dvx_ratio * 100))
        else:
            pass


def calc_delta_x1_esr_2(line, ctx):
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if 'x1_obj' not in ctx:
        ctx['x1_obj'] = dict()
    if 'esr_obj' not in ctx:
        ctx['esr_obj'] = dict()

    if 'x1.' in cols[2]:
        id = int(cols[2].split('.')[-1])
        if id not in ctx['match_tree']:
            return

        y = float(cols[3])
        x = float(cols[4])
        vlon_rel = float(cols[5])
        # ttc = float(cols[6])
        # range_rate =
        ctx['x1_obj'][id] = {'ts': ts, 'pos_lat': y, 'pos_lon': x, 'vel_lon': vlon_rel}
    elif 'esr.' in cols[2]:
        id = int(cols[2].split('.')[-1])
        find = False
        for x in ctx['match_tree']:
            if id in ctx['match_tree'][x]:
                find = True
                break
        if not find:
            return

        r = float(cols[3])
        a = float(cols[4])
        range_rate = float(cols[5])
        y = float(cols[6])
        ctx['esr_obj'][id] = {'ts': ts, 'range': r, 'angle': a, 'range_rate': range_rate, 'pos_lat': y}
    else:
        return

    lines = ''
    # print(ctx['x1_obj'], ctx['esr_obj'])
    for x1_id in ctx['x1_obj']:
        for esr_id in ctx['esr_obj']:
            esr_obs = ctx['esr_obj'][esr_id]
            x1_obs = ctx['x1_obj'][x1_id]
            ts = esr_obs['ts']
            if esr_id not in ctx['match_tree'][x1_id]:
                # print('invalid 1')
                return
            if ctx['match_tree'][x1_id][esr_id]['count'] <= 1:
                # print('invalid 2', x1_id, esr_id)
                return
            if ts > ctx['match_tree'][x1_id][esr_id]['end_ts']:
                # print('invalid 3', ts, ctx['match_tree'][x1_id][esr_id]['end_ts'])
                return
            if ts < ctx['match_tree'][x1_id][esr_id]['start_ts']:
                # print('invalid 4', ts, ctx['match_tree'][x1_id][esr_id]['start_ts'])
                return
            # print(ctx['x1_obj'], ctx['esr_obj'])
            if fabs(x1_obs['ts'] - esr_obs['ts']) > 0.2:
                # print('invalid 5')
                return

            # if x1_id not in ctx['matched']:
            #     ctx['matched'][x1_id] = list()
            # ctx['matched'][x1_id].append(esr_id)
            # ctx['matched']['esr'].add(ctx['esr_obj']['id'])
            if not ctx.get('dx'):
                ctx['dx'] = []
            if not ctx.get('dy'):
                ctx['dy'] = []
            if not ctx.get('dvx'):
                ctx['dvx'] = []
            if not ctx.get('pct_dx'):
                ctx['pct_dx'] = []
            if not ctx.get('pct_dy'):
                ctx['pct_dy'] = []
            if not ctx.get('pct_dvx'):
                ctx['pct_dvx'] = []
            # print('matched.', ctx['x1_obj'], ctx['esr_obj'])
            dx = x1_obs['pos_lon'] - esr_obs['range']
            dx_ratio = fabs(dx / esr_obs['range']) if esr_obs['range'] != 0 else 0
            dy = x1_obs['pos_lat'] - esr_obs['pos_lat']
            dy_ratio = fabs(dy / esr_obs['pos_lat']) if esr_obs['pos_lat'] != 0 else 0
            dvx = x1_obs['vel_lon'] - esr_obs['range_rate']
            dvx_ratio = fabs(dvx / esr_obs['range_rate']) if esr_obs['range_rate'] != 0 else 0
            ctx['dx'].append(dx)
            ctx['dy'].append(dy)
            ctx['dvx'].append(dvx)
            ctx['pct_dx'].append(dx_ratio * 100)
            ctx['pct_dy'].append(dy_ratio * 100)
            ctx['pct_dvx'].append(dvx_ratio * 100)
            # ctx['end_ts'] = ts
            # if not ctx.get('start_ts'):
            #     ctx['start_ts'] = ts
            print('delta calculating', x1_id, esr_id)
            line = compose_log(ts, 'match.x1_esr.{}.{}'.format(x1_id, esr_id), '{} {} {} {} {} {}'.format(
                dx, dy, dvx, dx_ratio * 100, dy_ratio * 100, dvx_ratio * 100))
            print(line)
            lines += line

    # print(lines)
    return lines


def calc_delta_x1_esr_3(line, ctx):
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if 'x1.' in cols[2]:
        id = int(cols[2].split('.')[-1])
        if id != ctx.get('x1_tgt'):
            return

        y = float(cols[3])
        x = float(cols[4])
        vlon_rel = float(cols[5])
        ttc = float(cols[6])
        # range_rate =
        ctx['x1_obj'] = {'ts': ts, 'id': id, 'pos_lat': y, 'pos_lon': x, 'vel_lon': vlon_rel, 'ttc': ttc}
    elif 'esr.' in cols[2]:
        id = int(cols[2].split('.')[-1])
        if id != ctx.get('esr_tgt'):
            return

        y = float(cols[3])
        x = float(cols[4])
        range_rate = float(cols[5])
        ttc = float(cols[6])
        ctx['esr_obj'] = {'ts': ts, 'id': id, 'pos_lat': y, 'pos_lon': x, 'range_rate': range_rate, 'ttc': ttc}
    else:
        return

    if 'x1_obj' in ctx and 'esr_obj' in ctx:
        x1_id = ctx['x1_obj']['id']
        esr_id = ctx['esr_obj']['id']
        if esr_id not in ctx['match_tree'][x1_id]:
            return
        if ctx['match_tree'][x1_id][esr_id]['count'] <= 1:
            return
        if ts > ctx['match_tree'][x1_id][esr_id]['end_ts']:
            return
        if ts < ctx['match_tree'][x1_id][esr_id]['start_ts']:
            return
        # print(ctx['x1_obj'], ctx['esr_obj'])
        if fabs(ctx['x1_obj']['ts'] - ctx['esr_obj']['ts']) > 0.2:
            return

        # if x1_id not in ctx['matched']:
        #     ctx['matched'][x1_id] = list()
        # ctx['matched'][x1_id].append(esr_id)
        # ctx['matched']['esr'].add(ctx['esr_obj']['id'])
        if not ctx.get('dx'):
            ctx['dx'] = []
        if not ctx.get('dy'):
            ctx['dy'] = []
        if not ctx.get('dvx'):
            ctx['dvx'] = []
        if not ctx.get('pct_dx'):
            ctx['pct_dx'] = []
        if not ctx.get('pct_dy'):
            ctx['pct_dy'] = []
        if not ctx.get('pct_dvx'):
            ctx['pct_dvx'] = []
        # print('matched.', ctx['x1_obj'], ctx['esr_obj'])
        dx = ctx['x1_obj']['pos_lon'] - ctx['esr_obj']['pos_lon']
        dx_ratio = fabs(dx / ctx['esr_obj']['pos_lon']) if ctx['esr_obj']['pos_lon'] != 0 else 0
        dy = ctx['x1_obj']['pos_lat'] - ctx['esr_obj']['pos_lat']
        dy_ratio = fabs(dy / ctx['esr_obj']['pos_lat']) if ctx['esr_obj']['pos_lat'] != 0 else 0
        dvx = ctx['x1_obj']['vel_lon'] - ctx['esr_obj']['range_rate']
        dvx_ratio = fabs(dvx / ctx['esr_obj']['range_rate']) if ctx['esr_obj']['range_rate'] != 0 else 0
        ctx['dx'].append(dx)
        ctx['dy'].append(dy)
        ctx['dvx'].append(dvx)
        ctx['pct_dx'].append(dx_ratio * 100)
        ctx['pct_dy'].append(dy_ratio * 100)
        ctx['pct_dvx'].append(dvx_ratio * 100)
        ctx['end_ts'] = ts
        if not ctx.get('start_ts'):
            ctx['start_ts'] = ts
        return compose_log(ts, 'match.x1_esr.{}.{}'.format(x1_id, esr_id), '{} {} {} {} {} {}'.format(
            dx, dy, dvx, dx_ratio * 100, dy_ratio * 100, dvx_ratio * 100))


def calc_delta(line, ctx):
    type1, type2 = ctx.get('delta_names')
    obj1 = type1+'_obj'
    obj2 = type2+'_obj'
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if type1+'.' in cols[2]:
        id = int(cols[2].split('.')[-1])
        if id != ctx.get(type1+'_tgt'):
            return

        y = float(cols[3])
        x = float(cols[4])
        vlon_rel = float(cols[5])
        ttc = float(cols[6])
        # range_rate =
        ctx[obj1] = {'ts': ts, 'id': id, 'pos_lat': y, 'pos_lon': x, 'vel_lon': vlon_rel, 'ttc': ttc}
    elif type2+'.' in cols[2]:
        if 'vehstate' in cols[2]:
            return
        # print(line)
        id = int(cols[2].split('.')[-1])
        if id != ctx.get(type2+'_tgt'):
            return

        y = float(cols[3])
        x = float(cols[4])
        vlon_rel = float(cols[5])
        ttc = float(cols[6])
        ctx[obj2] = {'ts': ts, 'id': id, 'pos_lat': y, 'pos_lon': x, 'vel_lon': vlon_rel, 'ttc': ttc}
    else:
        return

    if obj1 in ctx and obj2 in ctx:
        obs1id = ctx[obj1]['id']
        obs2id = ctx[obj2]['id']
        # print(ctx['match_tree'])
        # print(obj1, obs1id, obj2, obs2id)
        if obs2id not in ctx['match_tree'][obs1id]:
            return
        if ctx['match_tree'][obs1id][obs2id]['count'] <= 1:
            return
        if ts > ctx['match_tree'][obs1id][obs2id]['end_ts']:
            return
        if ts < ctx['match_tree'][obs1id][obs2id]['start_ts']:
            return
        # print(ctx[obj1], ctx[obj2])
        if fabs(ctx[obj1]['ts'] - ctx[obj2]['ts']) > 0.2:
            return

        # if obs1id not in ctx['matched']:
        #     ctx['matched'][obs1id] = list()
        # ctx['matched'][obs1id].append(obs2id)
        # ctx['matched']['esr'].add(ctx[obj2]['id'])
        if not ctx.get('dx'):
            ctx['dx'] = []
        if not ctx.get('dy'):
            ctx['dy'] = []
        if not ctx.get('dvx'):
            ctx['dvx'] = []
        if not ctx.get('dttc'):
            ctx['dttc'] = []
        if not ctx.get('pct_dx'):
            ctx['pct_dx'] = []
        if not ctx.get('pct_dy'):
            ctx['pct_dy'] = []
        if not ctx.get('pct_dvx'):
            ctx['pct_dvx'] = []
        if not ctx.get('pct_dttc'):
            ctx['pct_dttc'] = []
        # print('matched.', ctx[obj1], ctx[obj2])
        dx = ctx[obj1]['pos_lon'] - ctx[obj2]['pos_lon']
        dx_ratio = fabs(dx / ctx[obj2]['pos_lon']) if ctx[obj2]['pos_lon'] != 0 else 0
        dy = ctx[obj1]['pos_lat'] - ctx[obj2]['pos_lat']
        dy_ratio = fabs(dy / ctx[obj2]['pos_lat']) if ctx[obj2]['pos_lat'] != 0 else 0
        dvx = ctx[obj1]['vel_lon'] - ctx[obj2]['vel_lon']
        dvx_ratio = fabs(dvx / ctx[obj2]['vel_lon']) if ctx[obj2]['vel_lon'] != 0 else 0
        dttc = ctx[obj1]['ttc'] - ctx[obj2]['ttc']
        dttc_ratio = fabs(dttc / ctx[obj2]['ttc']) if ctx[obj2]['ttc'] != 0 else 0
        ctx['dx'].append(dx)
        ctx['dy'].append(dy)
        ctx['dvx'].append(dvx)
        ctx['dttc'].append(dttc)
        ctx['pct_dx'].append(dx_ratio * 100)
        ctx['pct_dy'].append(dy_ratio * 100)
        ctx['pct_dvx'].append(dvx_ratio * 100)
        ctx['pct_dttc'].append(dttc_ratio * 100)
        ctx['end_ts'] = ts
        if not ctx.get('start_ts'):
            ctx['start_ts'] = ts
        return compose_log(ts, 'match.{}_{}.{}.{}'.format(type1, type2, obs1id, obs2id), '{} {} {} {} {} {}'.format(
            dx, dy, dvx, dx_ratio * 100, dy_ratio * 100, dvx_ratio * 100))

# deprecated
# def batch_process(dir_name, parsers):
#     import pickle
#     dirs = os.listdir(dir_name)
#     analysis_dir = os.path.join(dir_name, 'analysis')
#     if not os.path.exists(analysis_dir):
#         os.mkdir(analysis_dir)
#
#     print('entering dir', dir_name)
#     targets = os.path.join(dir_name, 'targets.txt')
#     print('targets file:', targets)
#
#     with open(targets) as rf:
#         for line in rf:
#             # print(line)
#             cols = line.split('\t')
#             d = cols[0]
#             if d in dirs:
#                 print('entering data dir', d)
#                 try:
#                     if ',' in cols[1]:
#                         x1_target = [int(x) for x in cols[1].split(',')]
#                     else:
#                         x1_target = [int(cols[1])]
#                     if ',' in cols[2]:
#                         radar_target = [int(x) for x in cols[2].split(',')]
#                     else:
#                         radar_target = [int(cols[2])]
#                     start_frame = int(cols[3])
#                     end_frame = int(cols[4])
#                 except Exception as e:
#                     print(e)
#                     continue
#                 ctx = dict()
#                 data_dir = os.path.join(dir_name, d)
#                 log = os.path.join(data_dir, 'log.txt')
#                 ctx['radar_target'] = radar_target
#                 ctx['x1_target'] = x1_target
#
#                 ctx['can_port'] = {'esr': 'CAN1', 'x1': 'CAN0'}
#
#                 r = process_log(log, parsers, ctx, start_frame, end_frame)
#                 r = time_sort(r)
#                 rfile = shutil.copy2(r, data_dir)
#                 ts0 = ctx.get('ts0') or 0
#                 r = process_log(rfile, [pair_x1_esr], ctx)
#
#                 sts = ctx.get('start_ts')
#                 ets = ctx.get('end_ts')
#
#                 fig = visual.get_fig()
#                 samples = {'esr.obj.{}'.format(radar_target): {'x': 0}, 'x1.*.{}'.format(x1_target): {'x': 1}}
#                 visual.scatter(fig, rfile, samples, 'x(m)', ts0, sts, ets, False)
#                 samples = {'esr.obj.{}'.format(radar_target): {'y': 3}, 'x1.*.{}'.format(x1_target): {'y': 0}}
#                 visual.scatter(fig, rfile, samples, 'y(m)', ts0, sts, ets, False)
#                 samples = {'esr.obj.{}'.format(radar_target): {'Vx': 2}, 'x1.*.{}'.format(x1_target): {'Vx': 2}}
#                 visual.scatter(fig, rfile, samples, 'Vx(m/s)', ts0, sts, ets, False)
#                 pickle.dump(fig, open(os.path.join(analysis_dir, '{}_xyvx.pyfig'.format(d)), 'wb'))
#                 fig.savefig(os.path.join(analysis_dir, '{}_xyvx.png'.format(d)), dpi=300)
#                 # fig.savefig(os.path.join(analysis_dir, '{}_xyvx.svg'.format(d)), dpi=300)
#                 visual.close_fig(fig)
#
#                 fig = visual.get_fig()
#                 samples = {'match.x1_esr': {'dx': 0, 'dy': 1, 'dvx': 2}}
#                 visual.scatter(fig, r, samples, 'error', ts0, sts, ets, False)
#                 samples = {'match.x1_esr': {'dx_ratio': 3, 'dy_ratio': 4, 'dvx_ratio': 5}}
#                 visual.scatter(fig, r, samples, 'error(percent)', ts0, sts, ets, False)
#
#                 pickle.dump(fig, open(os.path.join(analysis_dir, '{}_error.pyfig'.format(d)), 'wb'))
#                 fig.savefig(os.path.join(analysis_dir, '{}_error.png'.format(d)), dpi=300)
#                 # fig.savefig(os.path.join(analysis_dir, '{}_error.svg'.format(d)), dpi=300)
#                 visual.close_fig(fig)
#                 rmse_x = np.sqrt(((np.array(ctx['dx'])) ** 2).mean())
#                 pct_dx = np.mean(ctx['pct_dx'])
#                 rmse_y = np.sqrt(((np.array(ctx['dy'])) ** 2).mean())
#                 pct_dy = np.mean(ctx['pct_dy'])
#                 rmse_vx = np.sqrt(((np.array(ctx['dvx'])) ** 2).mean())
#                 pct_dvx = np.mean(ctx['pct_dvx'])
#                 with open(os.path.join(analysis_dir, '{}_error.csv'.format(d)), 'w+') as wf:
#                     wf.write('Param\tRMSE\tError_percent\n')
#                     wf.write('x(m)\t{}\t{:.2f}%\n'.format(rmse_x, pct_dx))
#                     wf.write('y(m)\t{}\t{:.2f}%\n'.format(rmse_y, pct_dy))
#                     wf.write('Vx(m/s)\t{}\t{:.2f}%\n'.format(rmse_vx, pct_dvx))


# deprecated
def batch_process_1(dir_name, parsers):
    dirs = os.listdir(dir_name)
    for d in dirs:
        if not os.path.isdir(os.path.join(dir_name, d)):
            continue
        log = os.path.join(dir_name, d, 'pcc_data', 'log.txt')
        print(bcl.BOLD + bcl.HDR + 'Entering dir: ' + d + bcl.ENDC)
        single_process(log, parsers, False)


# deprecated
def batch_process_2(dir_name, parsers):
    dirs = os.listdir(dir_name)
    for d in dirs:
        if not os.path.isdir(os.path.join(dir_name, d)):
            continue
        log = os.path.join(dir_name, d, 'log.txt')
        print(bcl.BOLD + bcl.HDR + 'Entering dir: ' + d + bcl.ENDC)
        single_process(log, parsers, False)


def batch_process_3(dir_name, sensors, process, parsers=None, odir=None):
    for root, dirs, files in os.walk(dir_name):
        for f in files:
            if f == 'log.txt':
                odir = os.path.join(odir, os.path.basename(root)) if odir else None
                log = os.path.join(root, f)
                print(bcl.BOLD + bcl.HDR + '\nEntering dir: ' + root + bcl.ENDC)
                process(log, sensors, parsers, False, analysis_dir=odir)


def collect_result(dir_name):
    dirs = os.listdir(dir_name)
    analysis_dir = os.path.join(dir_name, 'analysis')
    if not os.path.exists(analysis_dir):
        os.mkdir(analysis_dir)
    for d in dirs:
        if not os.path.isdir(os.path.join(dir_name, d)):
            continue
        src_dir = os.path.join(dir_name, d, 'pcc_data', 'analysis')
        new_dir = os.path.join(analysis_dir, d)
        if os.path.exists(src_dir) and not os.path.exists(new_dir):
            shutil.copytree(src_dir, new_dir)
        else:
            print('dir not found:', src_dir)


def get_matches_from_pairs(matched_ep, names):
    type1, type2 = names
    matches = dict()
    # match_file = open(os.path.join(analysis_dir, 'log_match.txt'), 'w')
    for ts in sorted(matched_ep):
        # print(m, matched_ep[m])
        for obs1id in matched_ep[ts]:
            # x1id = pair['x1']['id']
            entry = matched_ep[ts][obs1id]
            obs2id = entry[type2]['id'] if type2 in entry else None
            # q3id = entry['q3']['id'] if 'q3' in entry else None
            # obs2id = ['id']
            # obs1id = pair.get()
            if obs2id is None:
                continue
            if obs1id not in matches:
                matches[obs1id] = dict()
            if obs2id not in matches[obs1id]:
                matches[obs1id][obs2id] = dict()
            if 'start_ts' not in matches[obs1id][obs2id]:
                matches[obs1id][obs2id]['start_ts'] = ts
            else:
                matches[obs1id][obs2id]['end_ts'] = ts
            if 'count' not in matches[obs1id][obs2id]:
                matches[obs1id][obs2id]['count'] = 0
            if 'dist_mean' not in matches[obs1id][obs2id]:
                matches[obs1id][obs2id]['dist_mean'] = 0
            dist = entry[type2]['dist']
            matches[obs1id][obs2id]['count'] += 1
            matches[obs1id][obs2id]['dist_mean'] += dist
            # print(ts, 'x1', obs1id, 'esr', obs2id)
    # matches[obs1id][obs2id]['dist_mean'] /= matches[obs1id][obs2id]['count']

    # screen matches
    for id1 in list(matches):
        for id2 in list(matches[id1]):
            entry = matches[id1][id2]
            matches[id1][id2]['dist_mean'] /= entry['count']
            if entry['count'] < 20:

                del matches[id1][id2]
                continue
            if entry['dist_mean'] > 5.0:
                del matches[id1][id2]
                continue
            sts = entry.get('start_ts')
            ets = entry.get('end_ts')
            if not sts or not ets or ets - sts < 1.0:
                del matches[id1][id2]
                continue
    return matches


def get_trajectory_from_matches(matches, types):
    trj_list = list()
    type1, type2 = types
    # match_dict = {}
    for obs1id in matches:
        # if obs1id == 43:
        #     print(matches[obs1id])
        if len(matches[obs1id]) == 1:
            obs2id = list(matches[obs1id])[0]
            entry = matches[obs1id][obs2id]
            trj = {'obs': {type1: [obs1id], type2: [obs2id]}, **entry}
            trj_list.append(trj)
            continue
        discard_list = list()
        for idx, obs2id1 in enumerate(sorted(matches[obs1id])):
            for obs2id2 in sorted(matches[obs1id])[idx+1:]:
                entry1 = matches[obs1id][obs2id1]
                entry2 = matches[obs1id][obs2id2]
                sts1 = entry1.get('start_ts')
                ets1 = entry1.get('end_ts')
                sts2 = entry2.get('start_ts')
                ets2 = entry2.get('end_ts')
                cnt1 = entry1.get('count')
                cnt2 = entry2.get('count')

                if not (sts1 and sts2 and ets2 and ets1 and cnt1 and cnt2):
                    continue

                # trj = None
                if sts1 <= ets2 and sts2 <= ets1:  # overlapped
                    if entry1['dist_mean'] > entry2['dist_mean'] + 1.0:
                        # trj = {'obs': {type1: [obs1id], type2: [obs2id2]}, **entry2}
                        discard_list.append(obs2id1)
                    elif entry2['dist_mean'] > entry1['dist_mean'] + 1.0:
                        # trj = {'obs': {type1: [obs1id], type2: [obs2id1]}, **entry1}
                        discard_list.append(obs2id2)
                    # trj_list.append(trj)

                # elif sts1-ets2 < 0.8 or sts2-ets1 < 0.8:  # no overlap
                    # trj = {'obs': {type1: [obs1id], type2: [obs2id1, obs2id2]},
                    #        'start_ts': min(sts1, sts2), 'end_ts': max(ets1, ets2),
                    #        'count': cnt1+cnt2,
                    #        'dist_mean': (entry1['dist_mean']*cnt1+entry2['dist_mean']*cnt2)/(cnt1+cnt2)}
                    # trj_list.append(trj)

                # if not trj:
                    # trj = {'obs': {type1: [obs1id], type2: [obs2id2]}, **entry2}
                    # trj_list.append(trj)
                    # trj = {'obs': {type1: [obs1id], type2: [obs2id1]}, **entry1}
                    # trj_list.append(trj)
                # if obs1id == 43:
                #     print('hahahahahahahah', trj)
            # match_dict['{}_{}'.format(obs1id, obs2id)] = entry
        for obs2id in list(matches[obs1id]):
            if obs2id in discard_list:
                print(bcl.BOLD+'discarded match:'+bcl.ENDC, type1, obs1id, type2, obs2id)
                del matches[obs1id][obs2id]
            else:
                trj = {'obs': {type1: [obs1id], type2: [obs2id]}, **(matches[obs1id][obs2id])}
                # print('lalala', trj)
                trj_list.append(trj)
    return trj_list


def get_traj_from_pairs(matched_ep, names):
    matches = get_matches_from_pairs(matched_ep, names)
    trj_list = get_trajectory_from_matches(matches, names)
    return trj_list

    # match_ids = list(match_dict)
    # for idx, ids1 in enumerate(match_ids):
    #     for ids2 in match_ids[idx:]:
    #         obs1id1, obs2id1 = map(int, ids1.split('_'))
    #         obs1id2, obs2id2 = map(int, ids2.split('_'))
    #         sts1 = match_dict[ids1]['start_ts']
    #         ets1 = match_dict[ids1]['end_ts']
    #         sts2 = match_dict[ids2]['start_ts']
    #         ets2 = match_dict[ids2]['end_ts']
    #         if sts1 > ets2 or ets1 < sts2:  # no overlap
    #             if obs1id1 == obs1id2 or obs2id1 == obs2id2:
    #                 trj.append({''})


def merge_trajectory(trj_list1, trj_list2):
    trj_list = list()
    # del_list_1 = list()
    # del_list_2 = list()
    for trj1 in trj_list1:
        for trj2 in trj_list2:
            if trj1['obs']['x1'][0] == trj2['obs']['x1'][0]:
                sts1 = trj1['start_ts']
                ets1 = trj1['end_ts']
                sts2 = trj2['start_ts']
                ets2 = trj2['end_ts']
                # print(trj1['obs'])
                # print(trj2['obs'])
                if sts1 <= ets2 and sts2 <= ets1:
                    a = dict()
                    a.update(trj1['obs'])
                    a.update(trj2['obs'])
                    # print(obs)
                    trj = {'obs': a,
                           'start_ts': min(sts1, sts2), 'end_ts': max(ets1, ets2),
                           'count': trj1['count'] + trj2['count'],
                           # 'dist_mean': (trj1['dist_mean'] * trj1['count'] + trj2['dist_mean'] * trj2['count']) / (trj1['count'] + trj2['count']),
                           'dist_mean': max(trj1['dist_mean'], trj2['dist_mean'])
                           }
                    trj_list.append(trj)
                    trj1['selected'] = True
                    trj2['selected'] = True
                else:
                    trj_list.append(trj1)
                    trj_list.append(trj2)

    for trj1 in trj_list1:
        if not trj1.get('selected'):
            trj_list.append(trj1)
    for trj2 in trj_list2:
        if not trj2.get('selected'):
            trj_list.append(trj2)
    return trj_list


def chart_by_trj(trj_list, r0, ts0, vis=False):
    for trj in trj_list:
        obs_list = list()
        sts = trj.get('start_ts')
        ets = trj.get('end_ts')
        cnt = trj.get('count')
        analysis_dir = os.path.dirname(r0)
        # ts0 = ctx.get('ts0') or 0
        curve_items = list()
        # print(trj['obs'])
        for type in sorted(trj['obs'], reverse=True):  # x1 q3 esr ars rtk
            curve_items.append('{}{}'.format(type, trj['obs'][type]).replace(' ', ''))
            for id in trj['obs'][type]:
                pattern = '{}.*.{}'.format(type, id)
                obs_list.append(pattern)
        print(bcl.OKBL + 'matched {}:'.format(len(trj['obs'])) + bcl.ENDC, trj)
        fig = visual.get_fig()
        for idx, item in enumerate(obs_meas_display):
            samples = {x: {item: idx} for x in obs_list}  # {'esr.obj.2': {'pos_lat': 2}}
            visual.scatter(fig, r0, samples, item, ts0, sts, ets, vis)
        save_fig_path = os.path.join(analysis_dir, '_'.join(curve_items))
        fig.savefig(save_fig_path + '.png', dpi=300)
        pickle.dump(fig, open(save_fig_path + '.pyfig', 'wb'))
        visual.close_fig(fig)
        print('saving fig:', save_fig_path)
        # entry = matches_esr[x1id][esrid]
        # matches_esr[x1id][esrid]['dist_mean'] /= matches_esr[x1id][esrid]['count']
        # ctx['x1_tgt'] = x1id
        # ctx['esr_tgt'] = esrid
        # continue



def viz_2d_trj(r0, source='rtk.6', vis=True):
    from recorder.convert import ub482_defs, decode_with_def
    from tools.geo import gps_bearing, gps_distance

    xlist = []
    ylist = []
    trjs = {}
    obs_cnt = 0
    point0 = None
    with open(r0) as rf:
        for idx, line in enumerate(rf):
            cols = line.split(' ')
            ts_now = float(cols[0]) + float(cols[1]) / 1000000
            if 'pinpoint' in cols[2]:
                _, idx, kw = cols[2].split('.')
                src = _ + '.' + idx
                if src == source:
                    r = decode_with_def(ub482_defs, line)
                    point0 = r
            if 'bestpos' in cols[2]:
                _, idx, kw = cols[2].split('.')
                src = _ + '.' + idx
                sol_stt = cols[4]

                if src == source:
                    r = decode_with_def(ub482_defs, line)
                    if sol_stt not in trjs:
                        trjs[sol_stt] = {'x': [], 'y': [], 'cnt': 0}
                    trjs[sol_stt]['cnt'] += 1
                    obs_cnt += 1
                    if not r:
                        continue
                    if sol_stt == 'NONE':
                        continue
                    if not point0:
                        point0 = r

                    angle = gps_bearing(point0['lat'], point0['lon'], r['lat'], r['lon'])
                    range = gps_distance(point0['lat'], point0['lon'], r['lat'], r['lon'])
                    x = cos(angle * pi / 180.0) * range
                    y = sin(angle * pi / 180.0) * range
                    trjs[sol_stt]['x'].append(x)
                    trjs[sol_stt]['y'].append(y)
                    # xlist.append(x)
                    # ylist.append(y)
    for sol_stt in trjs:
        pct = trjs[sol_stt]['cnt'] / obs_cnt * 100.0
        print('#obs in rtk {}: {}  {:.2f}%'.format(sol_stt, trjs[sol_stt]['cnt'], pct))
    fig = visual.get_fig()
    # visual.trj_2d(fig, xlist, ylist, vis)
    visual.trj_2d(fig, trjs, vis)
    fig.close()


def process_error_by_matches(matches, names, r0, ts0, ctx, vis=False):
    type1, type2 = names
    ctx['match_tree'] = matches
    ctx['delta_names'] = names
    if ctx.get(type1+'_obj') is not None:
        del ctx[type1+'_obj']
    if ctx.get(type2+'_obj') is not None:
        del ctx[type2+'_obj']
    # print(matches)
    for obs1id in matches:
        for obs2id in matches[obs1id]:
            entry = matches[obs1id][obs2id]
            analysis_dir = os.path.dirname(r0)
            ctx[type1 + '_tgt'] = obs1id
            ctx[type2 + '_tgt'] = obs2id

            print('calculating deltas:', type1, obs1id, type2, obs2id)
            r1 = process_log(r0, [calc_delta], ctx, output=os.path.join(analysis_dir, '{}[{}]_{}[{}]_diff.txt'.format(type1, obs1id, type2, obs2id)))
            sts = entry.get('start_ts')
            ets = entry.get('end_ts')
            # cnt = entry.get('count')

            fig = visual.get_fig()
            samples = {'match.{}_{}.{}.{}'.format(type1, type2, obs1id, obs2id): {'dx': 0, 'dy': 1, 'dvx': 2}}
            visual.scatter(fig, r1, samples, 'error', ts0, sts, ets, vis)
            samples = {
                'match.{}_{}.{}.{}'.format(type1, type2, obs1id, obs2id): {'dx_ratio': 3, 'dy_ratio': 4,
                                                                           'dvx_ratio': 5}}
            visual.scatter(fig, r1, samples, 'error(percent)', ts0, sts, ets, vis)

            pickle.dump(fig, open(
                os.path.join(analysis_dir, '{}[{}]_{}[{}]_error.pyfig'.format(type1, obs1id, type2, obs2id)), 'wb'))
            fig.savefig(os.path.join(analysis_dir, '{}[{}]_{}[{}]_error.png'.format(type1, obs1id, type2, obs2id)),
                        dpi=300)
            # fig.savefig(os.path.join(analysis_dir, '{}_error.svg'.format(d)), dpi=300)
            visual.close_fig(fig)
            err_file = os.path.join(analysis_dir, '{}[{}]_{}[{}]_error.csv'.format(type1, obs1id, type2, obs2id))
            print('generating error analysis', err_file)
            rmse_x = np.sqrt(((np.array(ctx['dx'])) ** 2).mean())
            pct_dx = np.mean(ctx['pct_dx'])
            rmse_y = np.sqrt(((np.array(ctx['dy'])) ** 2).mean())
            pct_dy = np.mean(ctx['pct_dy'])
            rmse_vx = np.sqrt(((np.array(ctx['dvx'])) ** 2).mean())
            pct_dvx = np.mean(ctx['pct_dvx'])
            rmse_ttc = np.sqrt(((np.array(ctx['dttc'])) ** 2).mean())
            pct_dttc = np.mean(ctx['pct_dttc'])
            ctx['dx'].clear()
            ctx['dy'].clear()
            ctx['dvx'].clear()
            ctx['dttc'].clear()
            ctx['pct_dx'].clear()
            ctx['pct_dy'].clear()
            ctx['pct_dvx'].clear()
            ctx['pct_dttc'].clear()
            with open(err_file, 'w+') as wf:
                wf.write('Param\tRMSE\tError_percent\n')
                wf.write('x(m)\t{}\t{:.2f}%\n'.format(rmse_x, pct_dx))
                wf.write('y(m)\t{}\t{:.2f}%\n'.format(rmse_y, pct_dy))
                wf.write('Vx(m/s)\t{}\t{:.2f}%\n'.format(rmse_vx, pct_dvx))
                wf.write('TTC(s)\t{}\t{:.2f}%\n'.format(rmse_ttc, pct_dttc))


def process_by_matches(matches, names, r0, ts0, ctx, vis=False):
    type1, type2 = names
    for obs1id in matches:
        for obs2id in matches[obs1id]:
            entry = matches[obs1id][obs2id]
            analysis_dir = os.path.dirname(r0)
            ctx[type1+'_tgt'] = obs1id
            ctx[type2+'_tgt'] = obs2id
            r1 = process_log(r0, [calc_delta_x1_esr_3], ctx, output=os.path.join(analysis_dir, 'log_p1.txt'))
            sts = entry.get('start_ts')
            ets = entry.get('end_ts')
            cnt = entry.get('count')
            if not sts or not ets or not cnt:
                print(bcl.BOLD + 'discard match:' + bcl.ENDC, obs1id, obs2id, entry)
            if cnt < 20 or ets - sts < 1.0:
                print(bcl.BOLD + 'discard match:' + bcl.ENDC, obs1id, obs2id, entry)
                continue
            # print(bcl.OKBL + 'matched(x1/esr):' + bcl.ENDC, obs1id, obs2id, entry)
            fig = visual.get_fig()
            jlist = []
            samples = {'{}.obj.{}'.format(type1, obs2id): {'x': 1}, '{}.*.{}'.format(type2, obs1id): {'x': 1}}
            jlist.append(samples)
            visual.scatter(fig, r0, samples, 'x(m)', ts0, sts, ets, vis)
            samples = {'{}.obj.{}'.format(type1, obs2id): {'y': 0}, '{}.*.{}'.format(type2, obs1id): {'y': 0}}
            jlist.append(samples)
            visual.scatter(fig, r0, samples, 'y(m)', ts0, sts, ets, vis)
            samples = {'{}.obj.{}'.format(type1, obs2id): {'Vx': 2}, '{}.*.{}'.format(type2, obs1id): {'Vx': 2}}
            jlist.append(samples)
            visual.scatter(fig, r0, samples, 'Vx(m/s)', ts0, sts, ets, vis)
            samples = {'{}.obj.{}'.format(type1, obs2id): {'TTC_m': 3}, '{}.*.{}'.format(type2, obs1id): {'TTC': 3}}
            visual.scatter(fig, r0, samples, 'TTC(s)', ts0, sts, ets, False)
            jlist.append(samples)
            pickle.dump(fig, open(os.path.join(analysis_dir, '{}[{}]_{}[{}]_xyvx.pyfig'.format(type1, obs1id, type2, obs2id)), 'wb'))
            json.dump(jlist, open(os.path.join(analysis_dir, '{}[{}]_{}[{}]_xyvx.json'.format(type1, obs1id, type2, obs2id)), 'w+'),
                      indent=True)
            fig.savefig(os.path.join(analysis_dir, '{}[{}]_{}[{}]_xyvx.png'.format(type1, obs1id, type2, obs2id)), dpi=300)
            # fig.savefig(os.path.join(analysis_dir, '{}_xyvx.svg'.format(d)), dpi=300)
            visual.close_fig(fig)

            # if 'dx' not in ctx:
            #     print('error analysis not calculated. Abort plotting.')
            #     return

            fig = visual.get_fig()
            samples = {'match.{}_{}.{}.{}'.format(type1, type2, obs1id, obs2id): {'dx': 0, 'dy': 1, 'dvx': 2}}
            visual.scatter(fig, r1, samples, 'error', ts0, sts, ets, vis)
            samples = {
                'match.{}_{}.{}.{}'.format(type1, type2, obs1id, obs2id): {'dx_ratio': 3, 'dy_ratio': 4, 'dvx_ratio': 5}}
            visual.scatter(fig, r1, samples, 'error(percent)', ts0, sts, ets, vis)

            pickle.dump(fig, open(os.path.join(analysis_dir, '{}[{}]_{}[{}]_error.pyfig'.format(type1, obs1id, type2, obs2id)), 'wb'))
            fig.savefig(os.path.join(analysis_dir, '{}[{}]_{}[{}]_error.png'.format(type1, obs1id, type2, obs2id)), dpi=300)
            # fig.savefig(os.path.join(analysis_dir, '{}_error.svg'.format(d)), dpi=300)
            visual.close_fig(fig)
            err_file = os.path.join(analysis_dir, '{}[{}]_{}[{}]_error.csv'.format(type1, obs1id, type2, obs2id))
            print('generating error analysis', err_file)
            rmse_x = np.sqrt(((np.array(ctx['dx'])) ** 2).mean())
            pct_dx = np.mean(ctx['pct_dx'])
            rmse_y = np.sqrt(((np.array(ctx['dy'])) ** 2).mean())
            pct_dy = np.mean(ctx['pct_dy'])
            rmse_vx = np.sqrt(((np.array(ctx['dvx'])) ** 2).mean())
            pct_dvx = np.mean(ctx['pct_dvx'])
            ctx['dx'].clear()
            ctx['dy'].clear()
            ctx['dvx'].clear()
            ctx['pct_dx'].clear()
            ctx['pct_dy'].clear()
            ctx['pct_dvx'].clear()
            with open(err_file, 'w+') as wf:
                wf.write('Param\tRMSE\tError_percent\n')
                wf.write('x(m)\t{}\t{:.2f}%\n'.format(rmse_x, pct_dx))
                wf.write('y(m)\t{}\t{:.2f}%\n'.format(rmse_y, pct_dy))
                wf.write('Vx(m/s)\t{}\t{:.2f}%\n'.format(rmse_vx, pct_dvx))


def prep_analysis(log, ctx, anadir=None):
    from tools.log_info import get_can_ports_and_roles
    from tools.transform import Transform
    from config.config import CVECfg
    cfg = CVECfg()
    data_dir = os.path.dirname(log)
    # log = os.path.join(data_dir, 'log.txt')
    analysis_dir = anadir or os.path.join(data_dir, 'analysis')
    if not os.path.exists(analysis_dir):
        os.mkdir(analysis_dir)
    conf_path = os.path.join(os.path.dirname(log), 'config.json')
    install_path = os.path.join(os.path.dirname(log), 'installation.json')

    pnr = get_can_ports_and_roles(log)
    if not pnr:
        pnr['can_port'] = {'x1': 'CAN1', 'esr': 'CAN0'}
    ctx.update(pnr)
    if os.path.exists(conf_path):
        cfg.configs = json.load(open(conf_path))
    else:
        print('no config.json found in {}. exit.'.format(os.path.dirname(log)))
    if os.path.exists(install_path):
        cfg.installs = json.load(open(install_path))
        ctx['trans'] = Transform(cfg)
    else:
        print('no installation.json found in {}. exit.'.format(os.path.dirname(log)))
        return
    # print('preparing done.', ctx.keys())
    return analysis_dir


def init_sensor_ctx(sensors, ctx):
    ctx['obs_ep'] = dict().fromkeys(sensors)
    for key in ctx['obs_ep']:
        ctx['obs_ep'][key] = {'buff': deque(maxlen=10)}
    # ctx['obs_ep']['x1'] = {'buff': deque(maxlen=10)}
    ctx['sensors'] = sensors


parsers_choice = {'esr': parse_esr_line,
                      'ars': parse_ars_line,
                      'rtk': parse_rtk_target_ub482,
                      'x1': parse_x1_line,
                      'x1_fusion': parse_x1_fusion_line,
                      'q3': parse_q3_line}


def single_process(log, sensors=['x1', 'q3', 'esr', 'rtk'], parsers=None, vis=True, x1tgt=None, rdrtgt=None, analysis_dir=None):
    # log = os.path.join(dir_name, 'log.txt')
    import json
    ctx = dict()
    init_sensor_ctx(sensors, ctx)
    # ctx['sensors'].append('x1')

    if not parsers:
        parsers = [
            dummy_parser,
            match_obs,
            parse_nmea_line,
            parse_x1_line]
        for sensor in sensors:
            if parsers_choice.get(sensor):
                parsers.append(parsers_choice[sensor])

    if not os.path.exists(log):
        print(bcl.FAIL + 'Invalid data path. {} does not exist.'.format(log) + bcl.ENDC)
        return

    analysis_dir = prep_analysis(log, ctx, analysis_dir)
    log = strip_log(log)
    r = time_sort(log, output=os.path.join(analysis_dir, 'log_sort.txt'))
    r0 = process_log(r, parsers, ctx, output=os.path.join(analysis_dir, 'log_p0.txt'))
    ts0 = ctx.get('ts0') or 0
    for sensor in ctx['obs_ep']:
        kw = '{}_ids'.format(sensor)
        print(kw, ctx.get(kw))
    print('ts0:', ts0)

    matches = dict()
    for sensor in sensors:
        matches[sensor] = get_matches_from_pairs(ctx['matched_ep'], ('x1', sensor))

    trj_lists = dict()
    trj_list_comb = list()
    for sensor in sensors:
        trj_list = get_trajectory_from_matches(matches[sensor], ('x1', sensor))
        # print('trj_'+sensor+':', trj_list)
        trj_lists[sensor] = trj_list
        trj_list_comb = merge_trajectory(trj_list_comb, trj_list)

    print('trj_comb:')
    for trj in trj_list_comb:
        print(trj)

    chart_by_trj(trj_list_comb, r0, ts0)
    for sensor in sensors:
        process_error_by_matches(matches[sensor], ('x1', sensor), r0, ts0, ctx)


def aeb_test_analysis(dir_name):
    from tools import visual
    import xlwt
    # import openpyxl

    xl = xlwt.Workbook()
    style = xlwt.XFStyle()  # 创建一个样式对象，初始化样式

    al = xlwt.Alignment()
    al.horz = 0x02  # 设置水平居中
    al.vert = 0x01  # 设置垂直居中
    style.alignment = al

    sheet = xl.add_sheet('FCW')
    sheet.col(0).width = 450 * 20
    sheet.write_merge(0, 2, 0, 0, 'case', style=style)
    for idx, name in enumerate(['FCW1', 'FCW2', 'AEB']):
        # color = 'gray50' if idx % 2 == 0 else 'white'
        # pattern = xlwt.Pattern()
        # pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        # pattern.pattern_fore_colour = xlwt.Style.colour_map[color]
        # style.pattern = pattern
        i = idx * 10 + 1
        # print(i)
        sheet.write_merge(0, 0, i, i+8, name, style=style)
        sheet.write_merge(1, 2, i, i, 'ts', style=style)
        sheet.write_merge(1, 2, i+1, i+1, 'speed', style=style)
        sheet.write_merge(1, 1, i+2, i+4, 'X1', style=style)
        sheet.write_merge(1, 1, i+5, i+9, 'Fusion', style=style)
        sheet.write(2, i+2, 'id')
        sheet.write(2, i+3, 'PosX')
        sheet.write(2, i+4, 'TTC')
        sheet.write(2, i+5, 'id')
        sheet.write(2, i+6, 'v')
        sheet.write(2, i+7, 'x')
        sheet.write(2, i+8, 'a')
        sheet.write(2, i+9, 'ttc')

    ln = 2

    for root, dirs, files in os.walk(dir_name):
        for f in files:
            if f == 'log.txt':
                ctx = {}
                # ctx['d530'] = {'aeb_level': 0, 'xbr_acc': 0}
                # odir = os.path.join(odir, os.path.basename(root)) if odir else None
                log = os.path.join(root, f)
                print(bcl.BOLD + bcl.HDR + '\nEntering dir: ' + root + bcl.ENDC)
                sensors = ['x1', 'x1_fusion', 'ars', 'd530']
                init_sensor_ctx(sensors, ctx)
                parsers = [parse_x1_line,
                           parse_ars_line,
                           parse_d530_line,
                           parse_nmea_line]

                analysis_dir = prep_analysis(log, ctx)
                if 'd530' not in ctx['can_port']:
                    print('d530 not configured. check config.json.')
                    continue
                log = strip_log(log)
                r = time_sort(log, output=os.path.join(analysis_dir, 'log_sort.txt'))
                r0 = process_log(r, parsers, ctx, output=os.path.join(analysis_dir, 'log_p0.txt'))
                # print(ctx.keys())
                ln += 1
                sheet.write(ln, 0, os.path.basename(root))
                # sheet.
                if 'd530' not in ctx:
                    print('d530 data not found in log. leaving.')
                    continue
                d = ctx['d530']

                for idx, name in enumerate(['FCW1', 'FCW2', 'AEB']):
                    i = idx * 10 + 1
                    entry = name.lower()
                    try:
                        sheet.write(ln, i, d[entry]['ts'])
                        sheet.write(ln, i+1, d[entry]['speed']['gps']['speed'])
                        sheet.write(ln, i+2, d[entry]['x1']['id'])
                        sheet.write(ln, i+3, d[entry]['x1']['pos_lon'])
                        sheet.write(ln, i+4, d[entry]['x1']['TTC'])
                        sheet.write(ln, i+5, d[entry]['x1f']['id'])
                        sheet.write(ln, i+6, d[entry]['x1f']['vel_lon'])
                        sheet.write(ln, i+7, d[entry]['x1f']['pos_lon'])
                        sheet.write(ln, i+8, d[entry]['x1f']['acc_lon'])
                    except Exception as e:
                        print('error occurred when processing', r)
                        print(e)
                # sheet.write(ln, 9, d[entry]['x1f']['TTC'])

                # print(ctx['d530'])
                del ctx
                # process(log, sensors, parsers, False, analysis_dir=odir)

    xl.save(os.path.join(dir_name, 'fcw.xls'))


def change_main_video(dir_name, main_video_name):
    if not os.path.exists(os.path.join(dir_name, main_video_name)):
        print('no dir found named', main_video_name, 'in', dir_name)
        return

    configs = json.load(open(os.path.join(dir_name, 'config.json')))
    new_configs = []
    old_main_idx = 0
    #  change main tags in config.json
    for cfg in configs:
        new_configs.append(cfg)
        if 'msg_types' in cfg and main_video_name in cfg['msg_types']:
            if cfg['is_main']:
                print('the given name of device is already main.')
                return
            print('replacing main tag in config.json')
            new_configs[-1]['is_main'] = True
            # print(new_configs)

        elif cfg.get('is_main'):
            old_main_idx = cfg['idx']
            new_configs[-1]['is_main'] = False
    # os.remove(os.path.join(dir_name, 'config.json'))
    json.dump(new_configs, open(os.path.join(dir_name, 'config.json'), 'w'), indent=True)
    #  change video dir names
    os.rename(os.path.join(dir_name, 'video'), os.path.join(dir_name, 'video.{}'.format(old_main_idx)))
    os.rename(os.path.join(dir_name, main_video_name), os.path.join(dir_name, 'video'))
    #  change entries in log.txt
    wf = open(os.path.join(dir_name, 'log.txt.new'), 'w')
    with open(os.path.join(dir_name, 'log.txt')) as rf:
        for line in rf:
            cols = line.split(' ')
            if cols[2] == 'camera':
                cols[2] = 'video.{}'.format(old_main_idx)
            elif main_video_name in cols[2]:
                cols[2] = 'camera'
            wf.write(' '.join(cols))
    wf.close()
    os.remove(os.path.join(dir_name, 'log.txt'))
    os.rename(os.path.join(dir_name, 'log.txt.new'), os.path.join(dir_name, 'log.txt'))


if __name__ == "__main__":
    from tools import visual
    import sys
    import argparse

    local_path = os.path.split(os.path.realpath(__file__))[0]
    os.chdir(local_path)

    log = '/media/nan/860evo/data/20191218150228_ars_x1_fusion_aeb_15kmh_test/log.txt'
    parser = argparse.ArgumentParser(description="process CVE log.")

    parser.add_argument('input_path', nargs='?', default=log)
    parser.add_argument('-o', '--output', default=None)
    parser.add_argument('-t', '--target', help='target sensor for analyzing', default='x1')
    parser.add_argument('-q3', '--q3', help='indicator for q3 parsing', action="store_true")
    parser.add_argument('-fus', '--fusion', help='indicator for x1_fusion parsing', action="store_true")
    parser.add_argument('-rtk', '--rtk', help='indicator for rtk target parsing', action="store_true")
    parser.add_argument('-ars', '--ars', help='indicator for conti ars parsing', action="store_true")
    parser.add_argument('-esr', '--esr', help='indicator for aptiv esr parsing', action="store_true")
    parser.add_argument('-hil', '--hil', help='preprocess log for HIL replay', action="store_true")
    parser.add_argument('-vec', '--vector', help='preprocess log for vector canalyzer', action="store_true")
    parser.add_argument('-aeb', '--aeb', help='preprocess log for aeb control tuning', action="store_true")
    parser.add_argument('-trj', '--trj', help='visualize rtk trajectory', action="store_true")
    parser.add_argument('-cmain', '--changemain', default=None)

    args = parser.parse_args()
    sensors = []
    # if args.input_path:
    r = args.input_path
    t0 = time.time()

    if args.output:
        analysis_dir = args.output
    else:
        analysis_dir = os.path.join(os.path.dirname(r), 'analysis')
    # if not os.path.exists(analysis_dir):
    #     os.mkdir(analysis_dir)

    if args.hil:
        trans_to_hil(r, args.output)
    elif args.vector:
        ctx = {}
        if not os.path.exists(analysis_dir):
            os.mkdir(analysis_dir)
        ofile = os.path.join(analysis_dir, 'log_vector.asc')
        process_log(r, [trans_line_to_asc], ctx, output=ofile)
    elif args.aeb:
        aeb_test_analysis(r)
    elif args.changemain:
        change_main_video(r, args.changemain)
    elif args.trj:
        viz_2d_trj(r)
    else:
        sensors = ['x1']
        if args.q3:
            sensors.append('q3')
        if args.fusion:
            sensors.append('x1_fusion')
        if args.rtk:
            sensors.append('rtk')
        if args.esr:
            sensors.append('esr')
        if args.ars:
            sensors.append('ars')

        if not sensors:
            sensors = ['q3', 'esr', 'ars', 'rtk']
        print('sensors:', sensors)
        rdir = os.path.dirname(r)

        if r.endswith('log.txt'):
            print(bcl.WARN + 'Single process log: ' + r + bcl.ENDC)
            single_process(r, sensors, analysis_dir=analysis_dir)
        else:
            print(bcl.WARN + 'Batch process logs in: ' + r + bcl.ENDC)
            batch_process_3(r, sensors, single_process, odir=analysis_dir)

    dt = time.time() - t0
    print(bcl.WARN + 'Processing done. Time cost: {}s'.format(dt) + bcl.ENDC)
    # test_sort(r)
    #
    # rfile = shutil.copy2(r, rdir)
