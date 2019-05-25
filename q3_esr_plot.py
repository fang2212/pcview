import os
from collections import deque
from parsers.mobileye_q3 import parse_ifv300
from parsers.radar import parse_esr
from parsers.x1 import parse_x1
from matplotlib import pyplot as plt
import plot_tmp as tmp


def time_sort(file_name, sort_itv=8000):
    """
    sort the log lines according to timestamp.
    :param file_name: path of the log file
    :param sort_itv:
    :return: sorted file path

    """
    # rev_lines = []
    print('sorting...')
    past_lines = deque(maxlen=2 * sort_itv)
    wf = open('log_sort.txt', 'w')
    idx = 0
    with open(file_name) as rf:
        for idx, line in enumerate(rf):
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
    return os.path.abspath('log_sort.txt')


def parse_esr_q3_data(file_name, parms, q3_can_port='CAN0', esr_can_port='CAN3'):
    print('parsing q3 obj...')
    q_ctx = {}
    e_ctx = {}

    q3_data = []
    esr_data = []
    q3_id = parms['q3_id']
    esr_id = parms['esr_id']

    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if q3_can_port in cols[2]:
                can_id = int(cols[3], 16)
                buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                ret = parse_ifv300(can_id, buf, q_ctx)

                if not ret or ret['type'] != 'obstacle':
                    continue

                if isinstance(ret, list):
                    for r in ret:
                        if r['id'] != q3_id:
                            continue
                        d = {'ts': ts, 'rng': r['pos_lon'], 'ttc': None}
                        if 'TTC' in r:
                            d['ttc'] = ret['TTC']
                        q3_data.append()

                else:
                    if ret['id'] != q3_id:
                        continue
                    d = {'ts': ts, 'rng': ret['pos_lon'], 'ttc': None}
                    if 'TTC' in ret:
                        d['ttc'] = ret['TTC']
                    q3_data.append(d)
                    print('q3', ret)

            if esr_can_port in cols[2]:
                can_id = int(cols[3], 16)

                buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                r = parse_esr(can_id, buf, e_ctx)
                # print(can_port, buf, r)
                if r is None: continue
                for item in r:
                    if item['id'] != esr_id:
                        continue
                    d = {'ts': ts, 'rng': item['range'], 'ttc': None}
                    esr_data.append(d)
                print('esr', r)
    return q3_data, esr_data


def parse_esr_x1_data(file_name, parms, x1_can_port='CAN0', esr_can_port='CAN1'):
    print('parsing x1 obj...')
    x_ctx = {}
    e_ctx = {}
    x1_data = []
    esr_data = []
    x1_id = parms['x1_id']
    esr_id = parms['esr_id']

    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if x1_can_port in cols[2]:
                can_id = int(cols[3], 16)
                buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                data = parse_x1(can_id, buf, x_ctx)
                if data is None: continue
                if isinstance(data, list):
                    for item in data:
                        if 'cipv' in item:
                            print('x1 ---', item)

                        if item['id'] != x1_id:
                            continue
                        d = {'ts': ts, 'rng': item['pos_lon'], 'ttc': None}
                        if 'TTC' in item:
                            d['ttc'] = item['TTC']
                        x1_data.append(d)
                else:
                    if 'cipv' in data:
                        print('x1 ---', data)

                    if data['id'] != x1_id:
                        continue
                    d = {'ts': ts, 'rng': data['pos_lon'], 'ttc': None}
                    if 'TTC' in data:
                        d['ttc'] = data['TTC']
                    x1_data.append(d)



            if esr_can_port in cols[2]:
                can_id = int(cols[3], 16)
                buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                r = parse_esr(can_id, buf, e_ctx)

                # print(can_port, buf, r)
                if r is None: continue

                for item in r:
                    if 'cipo' in item and item['cipo']:
                        print('esr ---', item)

                    if item['id'] not in esr_id:
                        continue
                    d = {'ts': ts, 'rng': item['range'], 'ttc': None}
                    esr_data.append(d)

        return x1_data, esr_data


def plot(a, b, a_name, b_name, filepath):
    fig = plt.figure(figsize=(10, 10))
    ax1 = plt.subplot(211)
    ax1.plot([item['ts'] for item in a], [item['rng'] for item in a])
    ax1.plot([item['ts'] for item in b], [item['rng'] for item in b], '.')
    ax1.legend([a_name, b_name])
    ax1.set_ylabel('dist')
    ax1.grid()

    ts, sp = tmp.main()
    ax2 = plt.subplot(212, sharex=ax1)
    ax2.plot([item['ts'] for item in a], [item['ttc'] for item in a])
    ax2.plot(ts, sp)
    ax2.legend([a_name, 'speed'])
    ax2.set_ylabel('ttc & sp')
    ax2.grid()
    plt.tight_layout()
    plt.savefig(filepath + '.png')
    plt.show()


def plot_speed(file_name):

    x = []
    y = []
    with open(file_name) as rf:
        for line in rf:
            cols = line.strip().split()
            if 'gps-speed' in cols[2]:
                ts = float(cols[0]) + float(cols[1]) / 1000000
                sp = float(cols[3])
                x.append(ts)
                y.append(sp)

    fig = plt.figure(figsize=(10, 10))
    ax1 = plt.subplot(111)
    ax1.plot(x, y)
    ax1.set_title('gps-speed')
    plt.savefig(file_name+'.sp.png')
    plt.show()


if __name__ == "__main__":
    r = '/home/cao/桌面/江苏/20190524192702-case7/log.txt'
    # parms = {'q3_id': 8, 'esr_id': 48}
    # q3, esr = parse_esr_q3_data(r, parms)
    #
    parms = {'x1_id': 28, 'esr_id': [3]}
    x1, esr = parse_esr_x1_data(r, parms)
    plot(x1, esr, 'x1', 'esr', r)

    # plot_speed(r)
