import datetime

bds_offset = 18.0

pos_types = ['NONE', 'SINGLE', 'PSRDIFF', 'INS', 'RTKFIXED', 'RTKFLOAT', 'SINGLE_NO_HD', 'PSRDIFF_NO_HD', 'RTKFIXED_NO_HD', 'RTKFLOAT_NO_HD']

def parse_cgi220(msg_type, msg, ctx=None):
    # print(msg)
    if isinstance(msg, bytes):
        nmeastr = msg.decode()
    else:
        nmeastr = msg

    fields = nmeastr.split('*')[0].split(',')

    if nmeastr.startswith('$GNGGA') or nmeastr.startswith('$GPGGA'):
        pass

    elif nmeastr.startswith('$GPCHC'):
        r = dict()
        r['type'] = 'inspva'
        week = int(fields[1])
        tow = float(fields[2])
        r['ts'] = week * 604800 + tow + 315964800.0 - bds_offset
        r['yaw'] = float(fields[3])
        r['pitch'] = float(fields[4])
        r['roll'] = float(fields[5])
        r['w_x'] = float(fields[6])
        r['w_y'] = float(fields[7])
        r['w_z'] = float(fields[8])
        r['acc_x'] = float(fields[9])
        r['acc_y'] = float(fields[10])
        r['acc_z'] = float(fields[11])
        r['lat'] = float(fields[12])
        r['lon'] = float(fields[13])
        r['hgt'] = float(fields[14])
        r['vel_e'] = float(fields[15])
        r['vel_n'] = float(fields[16])
        r['vel_u'] = float(fields[17])
        r['vel'] = float(fields[18])
        r['#SVs'] = int(fields[19])
        r['#solSVs'] = int(fields[20])  #  aux ant sat num
        status = r['#SVs'] = int(fields[21])
        # r['pos_type'] = '0x{:x}'.format(status)
        if not status & 0x0f:
            r['pos_type'] = 'NONE' + ' 0x{:x}'.format(status)
        elif status & 0x0f == 1:
            r['pos_type'] = pos_types[status>>8]
        elif status & 0x0f == 2:
            r['pos_type'] = "INS_" + pos_types[status>>8]
        elif status & 0x0f == 3:
            r['pos_type'] = 'INS'
        # r['pos_type'] = status

        r['diff_age'] = int(fields[22])
        r['warning'] = int(fields[23])

        return r
