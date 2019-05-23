import os
from collections import deque
from parsers.mobileye_q3 import parse_ifv300
from parsers.radar import parse_esr
from matplotlib import pyplot as plt


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


def parse_data(file_name, parms, q3_can_port='CAN0', esr_can_port='CAN3'):
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
                    # print('q3', ret)

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
                # print('esr', r)
    return q3_data, esr_data

def plot():
    fig = plt.figure(figsize=(10,10))
    ax1 = plt.subplot(211)
    ax1.plot([item['ts'] for item in q3], [item['rng'] for item in q3])
    ax1.plot([item['ts'] for item in esr], [item['rng'] for item in esr])
    ax1.legend(['q3', 'esr'])
    ax1.set_ylabel('dist')
    ax1.grid()

    ax2 = plt.subplot(212, sharex=ax1)
    ax2.plot([item['ts'] for item in q3], [item['ttc'] for item in q3])
    ax2.legend(['q3'])
    ax2.set_ylabel('ttc')
    ax2.grid()
    plt.tight_layout()
    plt.savefig(r + '.png')
    plt.show()


if __name__ == "__main__":
    r = '/home/yj/bak/data/AEB/AEB_X1_test/20190412121015_CCRS_40kmh/log.txt'
    parms = {'q3_id': 1, 'esr_id': 6}
    q3, esr = parse_data(r, parms)
    plot()


