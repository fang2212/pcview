import os
import shutil
from collections import deque

from mobileye_q3 import parse_ifv300

def ifv300log2json(log_path):
    contents = None
    with open(log_path, 'r+') as fp:
        contents = fp.readlines()
    for line in contents:
        cols = line.split(' ')
        if cols[2] == 'camera':
            print(line, end='')
        if cols[2] == 'CAN0':
            can_id = int(cols[3], 16).to_bytes(4, 'little')
            data = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
            # print(cols, int(cols[3], 16), can_id, data)
            tmp = parse_ifv300(int(cols[3], 16), data)
            if tmp:
                print(cols[0], cols[1], tmp)


def time_sort(file_name, sort_itv=8000):
    """
    sort the log lines according to timestamp.
    :param file_name: path of the log file
    :param sort_itv:
    :return: sorted file path

    """
    # rev_lines = []
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


if __name__ == "__main__":
    # source = 'F:\\EyeQ3\\20190311160558\\log.txt'
    # source = 'E:\\temp\\log.txt'
    source = 'F:\\temp\\log.txt'
    # source = '/mnt/f/EyeQ3/20190311160558/log.txt'
    r_sort = os.path.join(os.path.dirname(source), 'log_sort.txt')
    if not os.path.exists(r_sort):
        sort_src = time_sort(source)
        shutil.copy2(sort_src, os.path.dirname(source))
        os.remove(sort_src)
    ifv300log2json(r_sort)