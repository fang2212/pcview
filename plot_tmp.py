import cantools
import json
import matplotlib.pyplot as plt
import os

db_x1 = cantools.database.load_file('dbc/MINIEYE_AEB_20190123.dbc', strict=False)

def parse_x1_data(pcc_dir, x1_can_port='CAN0'):

    assert os.path.exists(pcc_dir)
    files = os.listdir(pcc_dir)
    fr_ids = dict()
    for file_name in files:
        if not file_name.endswith('log.txt'):
            continue
        with open(os.path.join(pcc_dir, file_name)) as rf:
            for line in rf:
                line = line.strip()
                if line == '': continue
                cols = line.split(' ')
                ts = float(cols[0]) + float(cols[1]) / 1000000
                if x1_can_port in cols[2]:
                    can_id = int(cols[3], 16)
                    buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                    ids = [m.frame_id for m in db_x1.messages]
                    if can_id not in ids:
                        return None
                    r = db_x1.decode_message(can_id, buf)
                    if 'frameid_car' in r:
                        fr_ids[r['frameid_car']] = ts
    return fr_ids


def find_sp_ts_from_pcv(pcv_dir, pcc_ids):
    ts = []
    speed = []
    assert os.path.exists(pcv_dir)
    files = os.listdir(pcv_dir)
    files = sorted(files)
    for file_name in files:
        if not file_name.endswith('.txt'):
            continue
        with open(os.path.join(pcv_dir, file_name)) as rf:
            for line in rf:
                line = line.strip()
                if line == '': continue
                d = dict(json.loads(line))
                if 'frame_id' in d['camera'] and d['camera']['frame_id'] in pcc_ids and 'speed' in d:
                    ts.append(pcc_ids[d['camera']['frame_id']])
                    speed.append(d['speed']*3.6)
    return ts, speed


def main(pcc_dir, pcv_dir):
    fds = parse_x1_data(pcc_dir)
    print(list(fds)[:10])
    return find_sp_ts_from_pcv(pcv_dir, fds)


if __name__ == '__main__':
    main('/home/cao/桌面/江苏/0527/pcc/20190527172910-CC_range_5kmh',
         '/home/cao/桌面/江苏/0527/pcv/20190527172928_CC_range_5kmh')