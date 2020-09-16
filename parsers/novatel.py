import time

bds_offset = 18.0

def parse_novatel(msg_type, msg, ctx):
    try:
        if isinstance(msg, bytes):
            msg = msg.decode().strip()
        header, data = msg.split(';')
        hfields = header.split(',')
        fields = data.split(',')
    except Exception as e:
        print('error when parsing novatel:', e)
        return
    if not msg.startswith('#'):
        print('invalid novatel msg:', msg)
        return
    msg_name = hfields[0][1:]
    port = hfields[1]
    seq = int(hfields[2])
    idle_time = float(hfields[3])
    time_status = hfields[4]
    week = int(hfields[5])
    sec = float(hfields[6])
    rcv_status = int(hfields[7], 16)
    bd_offset = int(hfields[9])
    rsv = hfields[8]
    if not msg_type:
        msg_type = msg_name.lower()

    r = {}
    r['ts'] = week * 604800 + sec + 315964800.0 - bds_offset
    # print(time.localtime(r['ts']))

    if msg_type == 'drpva' or msg_type == 'drpvaa':
        r['type'] = 'inspva'

        r['sol_stat'] = fields[0]
        r['pos_type'] = fields[1]
        r['datum'] = fields[2]
        r['dr_age'] = float(fields[4])
        r['sol_age'] = float(fields[5])

        r['lat'] = float(fields[6])
        r['lon'] = float(fields[7])
        r['hgt'] = float(fields[8])
        r['undulation'] = float(fields[9])
        r['lat_sgm'] = float(fields[10])
        r['lon_sgm'] = float(fields[11])
        r['hgt_sgm'] = float(fields[12])

        r['vel_e'] = float(fields[13])
        r['vel_n'] = float(fields[14])
        r['vel_u'] = float(fields[15])
        r['vel_e_sgm'] = float(fields[16])
        r['vel_n_sgm'] = float(fields[17])
        r['vel_u_sgm'] = float(fields[18])

        r['yaw'] = float(fields[19])
        r['pitch'] = float(fields[20])
        r['roll'] = float(fields[21])
        r['yaw_sgm'] = float(fields[22])
        r['pitch_sgm'] = float(fields[23])
        r['roll_sgm'] = float(fields[24])

        return r
    elif msg_type == 'inspvaxa':
        r['type'] = 'inspva'
        r['sol_stat'] = fields[0]
        r['pos_type'] = fields[1]

        r['lat'] = float(fields[2])
        r['lon'] = float(fields[3])
        r['hgt'] = float(fields[4])
        r['undulation'] = float(fields[5])

        r['vel_n'] = float(fields[6])
        r['vel_e'] = float(fields[7])
        r['vel_u'] = float(fields[8])


        r['roll'] = float(fields[9])
        r['pitch'] = float(fields[10])
        r['yaw'] = float(fields[11])

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
        # print(r)
        return r
