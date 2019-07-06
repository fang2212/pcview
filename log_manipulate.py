import json
import os
import shutil
import time
from collections import deque
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
        return os.path.abspath(out_file)
        # sort_itv = 8000
    # rev_lines = []
    past_lines = deque(maxlen=2 * sort_itv)
    wf = open('/tmp/log_sort.txt', 'w')
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


def parse_rtk(file_name):
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


def parse_rtk_target(file_name):
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


def parse_esr_cipo(file_name, can_port='CAN3'):
    from parsers.radar import parse_esr
    print('parsing esr cipo...')
    ctx = {}
    out_file = '/tmp/log_esr_cipo.txt'
    wf = open(out_file, 'w')
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if can_port in cols[2]:
                can_id = int(cols[3], 16)
                buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                r = parse_esr(can_id, buf, ctx)
                # print(can_port, buf, r)
                if not r:
                    wf.write(' '.join(cols))
                    continue
                for item in r:
                    # print(item['cipo'])
                    if item.get('cipo'):
                        wf.write(compose_log(ts, 'esr.cipo', '{} {}'.format(item['id'], item['range'], item['angle'])))
            wf.write(' '.join(cols))
    wf.close()
    return os.path.abspath(out_file)


def parse_esr_line(line, ctx):
    from parsers.radar import parse_esr
    from math import sin, pi
    can_port = ctx['can_port']['esr']
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
            angle_rad = item['angle'] * pi / 180.0
            x = cos(angle_rad) * item['range']
            y = sin(angle_rad) * item['range']
            # lines += compose_log(ts, 'esr.obj.{}'.format(item['id']),
            #                      '{} {} {} {} {}'.format(item['range'], item['angle'], item['range_rate'], y, item['TTC_m']))
            lines += compose_log(ts, 'esr.obj.{}'.format(item['id']),
                                 '{} {} {} {}'.format(y, x, item['range_rate'], item['TTC_m']))
            ctx['esr_ids'].add(item['id'])
            item['pos_lat'] = y
            item['pos_lon'] = x
        ctx['esr_obs_ep'] = r
        ctx['esr_obs_ep_ts'] = ts
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
    can_port = ctx.get('can_port')['x1']
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
        if not ret:
            return
        # print(ret)
        lines = ''
        ctx['x1_obs_ep'] = ret
        ctx['x1_obs_ep_ts'] = ts
        for r in ret:
            lines += compose_log(ts, 'x1.{}.{}'.format(r['class'], r['id']),
                                 '{} {} {} {}'.format(r['pos_lat'], r['pos_lon'], (r['vel_lon']),
                                                      r.get('TTC') or 7.0))
            ctx['x1_ids'].add(r['id'])
        return lines
        # if isinstance(ret, list):
        #
        #
        # else:
        #     ctx['x1_ids'].add(ret['id'])
        #     return compose_log(ts, 'x1.{}.{}'.format(ret['class'], ret['id']),
        #                        '{} {} {} {}'.format(ret['pos_lat'], ret['pos_lon'], (ret['vel_lon']),
        #                                             ret.get('TTC')))


def parse_q3_line(line, ctx, can_port='CAN0'):
    from parsers.mobileye_q3 import parse_ifv300
    cols = line.split(' ')
    ts = float(cols[0]) + float(cols[1]) / 1000000
    if can_port in cols[2] or can_port.lower() in cols[2]:
        can_id = int(cols[3], 16)
        buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
        ret = parse_ifv300(can_id, buf, ctx)
        # print(can_port, buf, r)

        if not ret or ret['type'] not in ['obstacle', 'vehicle_state']:
            return

        if ret['type'] == 'vehicle_state':
            return compose_log(ts, 'q3.vehstate', '{} {}'.format(ret['speed'], ret['yaw_rate']))

        if isinstance(ret, list):
            lines = ''
            for r in ret:
                lines += compose_log(ts, 'q3.{}.{}'.format(r['class'], r['id']),
                                     '{} {}'.format(r['pos_lat'], r['pos_lon']))
            return lines
        else:
            return compose_log(ts, 'q3.{}.{}'.format(ret['class'], ret['id']),
                               '{} {}'.format(ret['pos_lat'], ret['pos_lon']))


def parse_nmea_line(line, ctx):
    from parsers.ublox import parse_ublox
    cols = line.split(' ')
    if cols[2] == 'NMEA':
        r = parse_ublox('NMEA', cols[3])
        if r and 'speed' in r:
            ctx['speed'] = r['speed']


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
            # if x1item['id'] == 2:
            #     print(x1item['id'], esr_t['id'], get_distance(x1item, esr_t),
            #           ctx['esr_obs_ep_ts'] - ctx['x1_obs_ep_ts'],
            #           len(x1), len(esr))
            #     print(x1item, esr_t)
            # print(get_distance(x1item, esr_t))
            if get_distance(obs1item, obs2t) > 6.0:
                # print('dist too large.', x1item['id'], esr_t['id'], get_distance(x1item, esr_t))
                continue
            # if fabs(esr_ts - x1_ts) > 0.2:
                # print('time diff too large.', x1item['id'], esr_t['id'], ctx['esr_obs_ep_ts'] - ctx['x1_obs_ep_ts'])
                # continue
            if obs2t['id'] not in obs2_cdt:
                obs2_cdt[obs2t['id']] = dict()
                obs2_cdt[obs2t['id']][obs1item['id']] = {'dist': get_distance(obs1item, obs2t)}
    for o2id in obs2_cdt:
        # print(eid)
        dist = 99
        o1sel = 0
        for o1id in obs2_cdt[o2id]:
            if obs2_cdt[o2id][o1id]['dist'] < dist:
                dist = obs2_cdt[o2id][o1id]['dist']
                o1sel = o1id
        # ts = x1_ts
        # pair = {'x1': o1sel, 'esr': o2id}
        for o1 in obs1:
            for o2 in obs2:
                if o1['id'] == o1sel and o2['id'] == o2id:
                    return o1, o2
        # pair.update(esr_cdt[eid][x1_sel])
        # return pair


def find_esr_by_x1(line, ctx):
    # from tools.match import is_near
    if not ctx.get('matched_ep'):
        ctx['matched_ep'] = dict()
    if 'x1_obs_ep_ts' not in ctx or 'esr_obs_ep_ts' not in ctx:
        return
    if ctx.get('esr_obs_ep_ts') == ctx.get('esr_obs_ep_ts_last') \
            and ctx.get('x1_obs_ep_ts') == ctx.get('x1_obs_ep_ts_last'):
        return
    # x1_dt = ctx['x1_obs_ep_ts'] - ctx['x1_obs_ep_ts_last'] if 'x1_obs_ep_ts_last' in ctx else None
    # esr_dt = ctx['esr_obs_ep_ts'] - ctx['esr_obs_ep_ts_last'] if 'esr_obs_ep_ts_last' in ctx else None
    # print(ctx['x1_obs_ep_ts'], 'x1 dt:', x1_dt, 'esr dt:', esr_dt)
    # print('ok')
    ctx['esr_obs_ep_ts_last'] = ctx['esr_obs_ep_ts']
    ctx['x1_obs_ep_ts_last'] = ctx['x1_obs_ep_ts']
    esr = ctx.get('esr_obs_ep')
    x1 = ctx.get('x1_obs_ep')
    if not x1 or not esr:
        return

    # pair_list = dict()
    esr_cdt = dict()
    for x1item in x1:
        if len(esr) > 0:
            esr_list = sorted(esr, key=lambda x: get_distance(x1item, x))
            esr_t = esr_list[0]
            # if x1item['id'] == 2:
            #     print(x1item['id'], esr_t['id'], get_distance(x1item, esr_t),
            #           ctx['esr_obs_ep_ts'] - ctx['x1_obs_ep_ts'],
            #           len(x1), len(esr))
            #     print(x1item, esr_t)
            # print(get_distance(x1item, esr_t))
            if get_distance(x1item, esr_t) > 5.0:
                # print('dist too large.', x1item['id'], esr_t['id'], get_distance(x1item, esr_t))
                continue
            if fabs(ctx['esr_obs_ep_ts'] - ctx['x1_obs_ep_ts']) > 0.2:
                # print('time diff too large.', x1item['id'], esr_t['id'], ctx['esr_obs_ep_ts'] - ctx['x1_obs_ep_ts'])
                continue
            if esr_t['id'] not in esr_cdt:
                esr_cdt[esr_t['id']] = dict()
            esr_cdt[esr_t['id']][x1item['id']] = {'dist': get_distance(x1item, esr_t)}
    for eid in esr_cdt:
        # print(eid)
        dist = 99
        x1_sel = 0
        for x1id in esr_cdt[eid]:
            if esr_cdt[eid][x1id]['dist'] < dist:
                dist = esr_cdt[eid][x1id]['dist']
                x1_sel = x1id
        ts = ctx['x1_obs_ep_ts']
        pair = {'x1': x1_sel, 'esr': eid}
        pair.update(esr_cdt[eid][x1_sel])
        ctx['matched_ep'][ts] = pair
        # print('matched:', pair)


def match_x1_esr(line, ctx):
    if 'x1_obs_ep_ts' not in ctx or 'esr_obs_ep_ts' not in ctx:
        return
    if not ctx.get('matched_ep'):
        ctx['matched_ep'] = dict()
    if ctx.get('esr_obs_ep_ts') == ctx.get('esr_obs_ep_ts_last') and \
            ctx.get('x1_obs_ep_ts') == ctx.get('x1_obs_ep_ts_last'):
        return

    if ctx.get('esr_obs_ep_ts') != ctx.get('esr_obs_ep_ts_last'):
        if 'esr_buff' not in ctx:
            ctx['esr_buff'] = deque(maxlen=10)
        esr = ctx.get('esr_obs_ep')
        ctx['esr_buff'].append((ctx['esr_obs_ep_ts'], esr))
        ctx['esr_obs_ep_ts_last'] = ctx['esr_obs_ep_ts']

    if ctx.get('x1_obs_ep_ts') != ctx.get('x1_obs_ep_ts_last'):
        if 'x1_buff' not in ctx:
            ctx['x1_buff'] = deque(maxlen=10)
        x1 = ctx.get('x1_obs_ep')
        ctx['x1_buff'].append((ctx['x1_obs_ep_ts'], x1))
        ctx['x1_obs_ep_ts_last'] = ctx['x1_obs_ep_ts']

    done = False
    for i in range(len(ctx['x1_buff']) - 1, 0, -1):
        for j in range(len(ctx['esr_buff']) - 1, 0, -1):
            ts = ctx['x1_buff'][i][0]
            ts0 = ctx['esr_buff'][j-1][0]
            ts1 = ctx['esr_buff'][j][0]
            if ts0 < ts <= ts1:
                x1_obs_t = ctx['x1_buff'][i][1]
                # print(len(ctx['x1_buff'][i][1]), len(ctx['esr_buff'][j][1]))
                if ts - ts0 > ts1 - ts:
                    dt = ts1 - ts
                    esr_obs_t = ctx['esr_buff'][j][1]
                else:
                    dt = ts - ts0
                    esr_obs_t = ctx['esr_buff'][j-1][1]

                if dt > 0.1:
                    done = True
                    break

                ret = spatial_match_obs(x1_obs_t, esr_obs_t)
                if not ret:
                    done = True
                    # print('no spatial match', len(x1_obs_t), len(esr_obs_t), ts - ts0, ts1 - ts)
                    break
                x1sel, esrsel = ret
                pair = {'x1': x1sel['id'], 'esr': esrsel['id']}
                # ctx['matched_ep'][ts] = pair
                ctx['matched_ep'][ts] = (x1sel, esrsel,)
                done = True
                break
        if done:
            break
    # x1_dt = ctx['x1_obs_ep_ts'] - ctx['x1_obs_ep_ts_last'] if 'x1_obs_ep_ts_last' in ctx else None
    # esr_dt = ctx['esr_obs_ep_ts'] - ctx['esr_obs_ep_ts_last'] if 'esr_obs_ep_ts_last' in ctx else None
    # print(ctx['x1_obs_ep_ts'], 'x1 dt:', x1_dt, 'esr dt:', esr_dt)
    # print('ok')




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
            obs1 = matched_ep[ts][0]
            obs2 = matched_ep[ts][1]
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


def batch_process_3(dir_name, parsers):
    for root, dirs, files in os.walk(dir_name):
        for f in files:
            if f == 'log.txt':
                log = os.path.join(root, f)
                print(bcl.BOLD + bcl.HDR + 'Entering dir: ' + root + bcl.ENDC)
                single_process(log, parsers, False)


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


def single_process(log, parsers, vis=True, x1tgt=None, rdrtgt=None):
    import pickle
    # log = os.path.join(dir_name, 'log.txt')
    ctx = dict()
    if not os.path.exists(log):
        print(bcl.FAIL + 'Invalid data path. {} does not exist.'.format(log) + bcl.ENDC)
        return
    conf_path = os.path.join(os.path.dirname(log), 'config.json')
    if os.path.exists(conf_path):
        conf = json.load(open(conf_path))
        canports = dict()
        for idx, collector in enumerate(conf):
            type0 = collector['can_types']['can0']
            if type0 and type0[0] not in canports:
                canports[type0[0]] = 'CAN{}'.format(idx * 2)
            type1 = collector['can_types']['can1']
            if type1 and type1[0] not in canports:
                canports[type1[0]] = 'CAN{}'.format(idx * 2 + 1)
        ctx['can_port'] = canports
        print(canports)
        # time.sleep(10)
    else:
        ctx['can_port'] = {'x1': 'CAN1',
                           'esr': 'CAN0'
                           }

    if rdrtgt is not None:
        ctx['radar_target'] = rdrtgt
    if x1tgt is not None:
        ctx['x1_target'] = x1tgt
    data_dir = os.path.dirname(log)
    # log = os.path.join(data_dir, 'log.txt')
    analysis_dir = os.path.join(data_dir, 'analysis')
    if not os.path.exists(analysis_dir):
        os.mkdir(analysis_dir)

    r = time_sort(log, output=os.path.join(analysis_dir, 'log_sort.txt'))
    r0 = process_log(r, parsers, ctx, output=os.path.join(analysis_dir, 'log_p0.txt'))

    # rfile = shutil.copy2(r, os.path.join(data_dir, 'log_process0.txt'))
    ts0 = ctx.get('ts0') or 0
    print('x1_ids:', ctx['x1_ids'])
    print('esr_ids:', ctx['esr_ids'])
    print('ts0:', ts0)

    matches = dict()
    # match_file = open(os.path.join(analysis_dir, 'log_match.txt'), 'w')
    for ts in sorted(ctx['matched_ep']):
        # print(m, ctx['matched_ep'][m])
        x1id = ctx['matched_ep'][ts][0]['id']
        esrid = ctx['matched_ep'][ts][1]['id']
        if x1id not in matches:
            matches[x1id] = dict()
        if esrid not in matches[x1id]:
            matches[x1id][esrid] = dict()
        if 'start_ts' not in matches[x1id][esrid]:
            matches[x1id][esrid]['start_ts'] = ts
        else:
            matches[x1id][esrid]['end_ts'] = ts
        if 'count' not in matches[x1id][esrid]:
            matches[x1id][esrid]['count'] = 0
        matches[x1id][esrid]['count'] += 1
    ctx['match_tree'] = matches
    # r1 = process_log(r0, [calc_delta_x1_esr], ctx, output=os.path.join(analysis_dir, 'log_p1.txt'))
    # r1 = calc_delta_x1_esr_1(ctx['matched_ep'], analysis_dir)
    # print('x1_targets:', x1_target)
    # print('radar_targets:', radar_target)
    # if len(x1_target) == 0:
    #     print('No x1 target selected, abort plotting.')
    #     return
    for x1id in matches:
        for esrid in matches[x1id]:
            ctx['x1_tgt'] = x1id
            ctx['esr_tgt'] = esrid
            r1 = process_log(r0, [calc_delta_x1_esr_3], ctx, output=os.path.join(analysis_dir, 'log_p1.txt'))
            sts = matches[x1id][esrid].get('start_ts')
            ets = matches[x1id][esrid].get('end_ts')
            cnt = matches[x1id][esrid].get('count')
            if not sts or not ets or not cnt:
                print(bcl.BOLD + 'discard match:' + bcl.ENDC, x1id, esrid, matches[x1id][esrid])
            if cnt < 10 or ets - sts < 1.0:
                print(bcl.BOLD + 'discard match:' + bcl.ENDC, x1id, esrid, matches[x1id][esrid])
                continue
            print(bcl.OKBL + 'matched(x1/esr):' + bcl.ENDC, x1id, esrid, matches[x1id][esrid])
            fig = visual.get_fig()
            jlist = []
            samples = {'esr.obj.{}'.format(esrid): {'x': 1}, 'x1.*.{}'.format(x1id): {'x': 1}}
            jlist.append(samples)
            visual.scatter(fig, r0, samples, 'x(m)', ts0, sts, ets, vis)
            samples = {'esr.obj.{}'.format(esrid): {'y': 0}, 'x1.*.{}'.format(x1id): {'y': 0}}
            jlist.append(samples)
            visual.scatter(fig, r0, samples, 'y(m)', ts0, sts, ets, vis)
            samples = {'esr.obj.{}'.format(esrid): {'Vx': 2}, 'x1.*.{}'.format(x1id): {'Vx': 2}}
            jlist.append(samples)
            visual.scatter(fig, r0, samples, 'Vx(m/s)', ts0, sts, ets, vis)
            samples = {'esr.obj.{}'.format(esrid): {'TTC_m': 3}, 'x1.*.{}'.format(x1id): {'TTC': 3}}
            visual.scatter(fig, r0, samples, 'TTC(s)', ts0, sts, ets, False)
            jlist.append(samples)
            pickle.dump(fig, open(os.path.join(analysis_dir, 'x1[{}]_esr[{}]_xyvx.pyfig'.format(x1id, esrid)), 'wb'))
            json.dump(jlist, open(os.path.join(analysis_dir, 'x1[{}]_esr[{}]_xyvx.json'.format(x1id, esrid)), 'w+'),
                      indent=True)
            fig.savefig(os.path.join(analysis_dir, 'x1[{}]_esr[{}]_xyvx.png'.format(x1id, esrid)), dpi=300)
            # fig.savefig(os.path.join(analysis_dir, '{}_xyvx.svg'.format(d)), dpi=300)
            visual.close_fig(fig)

            # if 'dx' not in ctx:
            #     print('error analysis not calculated. Abort plotting.')
            #     return

            fig = visual.get_fig()
            samples = {'match.x1_esr.{}.{}'.format(x1id, esrid): {'dx': 0, 'dy': 1, 'dvx': 2}}
            visual.scatter(fig, r1, samples, 'error', ts0, sts, ets, vis)
            samples = {
                'match.x1_esr.{}.{}'.format(x1id, esrid): {'dx_ratio': 3, 'dy_ratio': 4, 'dvx_ratio': 5}}
            visual.scatter(fig, r1, samples, 'error(percent)', ts0, sts, ets, vis)

            pickle.dump(fig, open(os.path.join(analysis_dir, 'x1[{}]_esr[{}]_error.pyfig'.format(x1id, esrid)), 'wb'))
            fig.savefig(os.path.join(analysis_dir, 'x1[{}]_esr[{}]_error.png'.format(x1id, esrid)), dpi=300)
            # fig.savefig(os.path.join(analysis_dir, '{}_error.svg'.format(d)), dpi=300)
            visual.close_fig(fig)
            # rmse_x = np.sqrt(((np.array(ctx['dx'])) ** 2).mean())
            # pct_dx = np.mean(ctx['pct_dx'])
            # rmse_y = np.sqrt(((np.array(ctx['dy'])) ** 2).mean())
            # pct_dy = np.mean(ctx['pct_dy'])
            # rmse_vx = np.sqrt(((np.array(ctx['dvx'])) ** 2).mean())
            # pct_dvx = np.mean(ctx['pct_dvx'])
            # with open(os.path.join(analysis_dir, 'x1[{}]_esr[{}]_error.csv'.format(x1id, esrid)), 'w+') as wf:
            #     wf.write('Param\tRMSE\tError_percent\n')
            #     wf.write('x(m)\t{}\t{:.2f}%\n'.format(rmse_x, pct_dx))
            #     wf.write('y(m)\t{}\t{:.2f}%\n'.format(rmse_y, pct_dy))
            #     wf.write('Vx(m/s)\t{}\t{:.2f}%\n'.format(rmse_vx, pct_dvx))


if __name__ == "__main__":
    from tools import visual
    import sys

    local_path = os.path.split(os.path.realpath(__file__))[0]
    os.chdir(local_path)
    # print('local_path:', local_path)
    r = '/media/nan/860evo/data/20190704-t5-q3-esr-x1-test/pc_colletor'

    if len(sys.argv) > 1:
        r = sys.argv[1]

    rdir = os.path.dirname(r)
    ts = time.time()

    parsers = [
        dummy_parser,
        match_x1_esr,
        parse_nmea_line,
        parse_esr_line,
        # parse_q3_line,
        parse_x1_line,
    ]

    if r.endswith('log.txt'):
        print(bcl.WARN + 'Single process log: ' + r + bcl.ENDC)
        single_process(r, parsers, False)
        # single_process(r, parsers, False, x1tgt=[6, 51], rdrtgt=[44])
    else:
        # batch_process(r, parsers)
        print(bcl.WARN + 'Batch process logs in: ' + r + bcl.ENDC)
        batch_process_3(r, parsers)

    dt = time.time() - ts
    print(bcl.WARN + 'Processing done. Time cost: {}s'.format(dt) + bcl.ENDC)
    # test_sort(r)
    #
    # rfile = shutil.copy2(r, rdir)
