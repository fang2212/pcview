import time

bds_offset = 18.0


pos_types = {
    'NONE': 0,
    'FIXEDPOS': 1,
    'FIXEDHEIGHT': 2,
    'DOPPLER_VELOCITY': 8,
    'SINGLE': 16,
    'PSRDIFF': 17,
    'WAAS': 18,
    'L1_FLOAT': 32,
    'IONOFREE_FLOAT': 33,
    'NARROW_FLOAT': 34,
    'L1_INT': 48,
    'WIDE_INT': 49,
    'NARROW_INT': 50,
    'INS': 52,
    'INS_PSRSP': 53,
    'INS_PSRDIFF': 54,
    'INS_RTKFLOAT': 55,
    'INS_RTKFIXED': 56
}


def parse_drpva(fields):
    if len(fields) < 28:
        print('drpva invalid length', fields)
        return

    r = {}
    # print(fields)
    r['type'] = 'drpva'

    r['sol_stat'] = fields[0]
    r['pos_type'] = fields[1]
    r['datum'] = fields[2]
    r['dr_age'] = float(fields[7])
    r['sol_age'] = float(fields[8])

    r['lat'] = float(fields[9])
    r['lon'] = float(fields[10])
    r['hgt'] = float(fields[11])
    r['undulation'] = float(fields[12])
    r['lat_sgm'] = float(fields[13])
    r['lon_sgm'] = float(fields[14])
    r['hgt_sgm'] = float(fields[15])

    r['vel_e'] = float(fields[16])
    r['vel_n'] = float(fields[17])
    r['vel_u'] = float(fields[18])
    r['vel_e_sgm'] = float(fields[19])
    r['vel_n_sgm'] = float(fields[20])
    r['vel_u_sgm'] = float(fields[21])

    r['yaw'] = float(fields[22])
    r['pitch'] = float(fields[23])
    r['roll'] = float(fields[24])
    r['yaw_sgm'] = float(fields[25])
    r['pitch_sgm'] = float(fields[26])
    r['roll_sgm'] = float(fields[27])

    return r


def parse_inspva(fields):
    if len(fields) < 22:
        print('inspva invalid length', fields)
        return
    r = {}
    r['type'] = 'inspva'
    r['sol_stat'] = fields[0]
    r['pos_type'] = 'INS' if fields[1] == '' else fields[1]

    r['lat'] = float(fields[2])
    r['lon'] = float(fields[3])
    r['hgt'] = float(fields[4])
    r['undulation'] = float(fields[5])
    # r['hgt'] = r['hgt'] - r['undulation']

    r['vel_n'] = float(fields[6])
    r['vel_e'] = float(fields[7])
    r['vel_u'] = float(fields[8])

    r['roll'] = float(fields[9])
    r['pitch'] = float(fields[10])
    r['yaw'] = float(fields[11])
    if r['yaw'] > 360.0:
        r['yaw'] = r['yaw'] - 360.0

    r['lat_sgm'] = float(fields[12])
    r['lon_sgm'] = float(fields[13])
    r['hgt_sgm'] = float(fields[14])

    r['vel_n_sgm'] = float(fields[15])
    r['vel_e_sgm'] = float(fields[16])
    r['vel_u_sgm'] = float(fields[17])

    r['roll_sgm'] = float(fields[19])
    r['pitch_sgm'] = float(fields[20])
    r['yaw_sgm'] = float(fields[21])

    # r['time_since_update'] = float(fields[22])
    # print(r)?
    return r


def parse_bestpos(fields):
    if len(fields) < 20:
        print('invalid bestpos:', fields)
        return
    r = {}
    r['type'] = 'bestpos'

    r['sol_stat'] = fields[0]
    r['pos_type'] = fields[1]
    r['lat'] = float(fields[2])
    r['lon'] = float(fields[3])
    r['hgt'] = float(fields[4])
    r['undulation'] = float(fields[5])
    r['datum'] = fields[6]
    r['lat_sgm'] = float(fields[7])
    r['lon_sgm'] = float(fields[8])
    r['hgt_sgm'] = float(fields[9])
    r['station_id'] = fields[10]
    r['diff_age'] = float(fields[11])
    r['sol_age'] = float(fields[12])
    r['#SVs'] = int(fields[13])
    r['#solSVs'] = int(fields[14])
    r['rsv1'] = int(fields[15])
    r['rsv2'] = int(fields[16])
    r['rsv3'] = int(fields[17])
    r['ext_sol_stat'] = int(fields[18], 16)
    r['rsv4'] = int(fields[19])
    # r['sig_mask'] = int(fields[20], 16)
    return r

#
# def parse_novatel(msg_type, msg, ctx=None):
#     if isinstance(msg, bytes):
#         msg = msg.decode().strip()
#     if not msg.startswith('#'):
#         return
#     results = []
#     for m in msg.split('#'):
#         if m:
#             try:
#                 ret = _parse_novatel(msg_type, '#'+m, ctx)
#                 if ret:
#                     results.append(ret)
#             except Exception as e:
#                 print('error when parsing novatel:\n', m)
#                 raise(e)
#
#     if len(results) > 0:
#         return results


def parse_novatel(msg_type, msg, ctx):
    if not msg.startswith('#'):
        print('invalid novatel msg:', msg)
        return
    # try:
    if isinstance(msg, bytes):
        msg = msg.decode().strip()
    header, data = msg.split(';')
    hfields = header.split(',')
    fields = data.split('*')[0].split(',')

    msg_name = hfields[0][1:]
    port = hfields[1]
    seq = int(hfields[2])
    idle_time = float(hfields[3])
    time_status = hfields[4]
    week = int(hfields[5])
    sec = float(hfields[6])
    rcv_status = int(hfields[7], 16)
    bd_offset = int(hfields[9])
    # print(bd_offset)
    rsv = hfields[8]
    if not msg_type:
        msg_type = msg_name.lower()

    # except Exception as e:
    #     print('error when parsing novatel:', msg)
    #     raise e

    r = {}
    r['type'] = msg_type
    r['ts'] = week * 604800 + sec + 315964800.0 - bds_offset
    # print(time.localtime(r['ts']))

    if msg_type == 'drpva' or msg_type == 'drpvaa':
        ret = parse_drpva(fields)
        # print(ret)
        r.update(ret)

    elif msg_type == 'inspvaxa':
        ret = parse_inspva(fields)
        r.update(ret)

    elif msg_type == 'corrimudataa':
        if len(fields) < 8:
            print('invalid corrimudate:', data)
            return
        r['type'] = 'imu_data_corrected'
        r['pitch_rate'] = float(fields[2])
        r['roll_rate'] = float(fields[3])
        r['yaw_rate'] = float(fields[4])
        r['acc_lat'] = float(fields[5])
        r['acc_lon'] = float(fields[6])
        r['acc_hgt'] = float(fields[7])

        return r

    elif msg_type == 'bestposa':
        ret = parse_bestpos(fields)
        r.update(ret)
    elif msg_type == 'bestgnssposa':
        # ret = parse_bestpos(fields)
        # r.update({'pos_type': ret['pos_type']})
        return
    if r:
        return r

