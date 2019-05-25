import cantools
import json
import matplotlib.pyplot as plt

db_x1 = cantools.database.load_file('dbc/MINIEYE_AEB_20190123.dbc', strict=False)

def parse_x1_data(file_name, x1_can_port='CAN0'):
    with open(file_name) as rf:
        fr_ids = dict()
        for line in rf:
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


def find_sp_ts_from_pcv(file_path, pcc_ids):

    ts = []
    speed = []
    with open(file_path) as rf:
        for line in rf:
            line = line.strip()
            d = dict(json.loads(line))
            if d['camera']['frame_id'] in pcc_ids:
                print(d['speed'], pcc_ids[d['camera']['frame_id']])
                ts.append(pcc_ids[d['camera']['frame_id']])
                speed.append(d['speed']*3.6)
    return ts, speed

def main():
    fds = parse_x1_data('/home/cao/桌面/江苏/20190524192702-case7/log.txt')
    return find_sp_ts_from_pcv('/home/cao/桌面/江苏/pcv/20190524192710/20190524192710.txt', fds)


if __name__ == '__main__':
    pass