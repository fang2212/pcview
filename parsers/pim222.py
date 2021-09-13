import datetime

pos_types = {0: 'NONE', 1: 'SINGLE', 2: 'INS_PSRDIFF', 4: 'INS_RTKFIXED', 5: 'INS_RTKFLOAT', 6: 'INS', 7: 'FIXEDPOS'}


def parse_pim222(msg_type, msg, ctx=None):
    if isinstance(msg, bytes):
        nmeastr = msg.decode()
    else:
        nmeastr = msg

    fields = nmeastr.split(',')

    if nmeastr.startswith('$GNGGA') or nmeastr.startswith('$GPGGA'):
        if ctx.get('disable_nmea'):
            return
        if any([not f for f in fields]):
            return
        r = dict()
        # print(nmeastr)
        r['type'] = 'gpgga'

        r['lat'] = int(fields[2][:2]) + float(fields[2][2:]) / 60.0
        r['lon'] = int(fields[4][:3]) + float(fields[4][3:]) / 60.0
        r['pos_type'] = pos_types.get(int(fields[6]))
        r['#SVs'] = int(fields[7])
        r['#solSVs'] = r['#SVs']
        r['hdop'] = float(fields[8])
        r['hgt'] = float(fields[9])
        r['undulation'] = float(fields[11])
        r['diff_age'] = float(fields[13]) if fields[13] else None
        # r['station_id'] = fields[14]
        if ctx and ctx.get('date'):
            str_time = ctx['date'] + ' ' + fields[1][:2] + ':' + fields[1][2:4] + ':' + fields[1][4:]
            dtime = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")
            dtime = dtime + datetime.timedelta(hours=8)
            r['ts'] = dtime.timestamp()
            # print(r['ts'])
        else:
            # str_time = '2020-11-10' + ' ' + fields[1][:2] + ':' + fields[1][2:4] + ':' + fields[1][4:]
            # dtime = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")
            # dtime = dtime + datetime.timedelta(hours=8)
            # r['ts'] = dtime.timestamp()
            return

        return r

    elif nmeastr.startswith('$GPZDA'):
        # r = dict()
        # print(nmeastr)
        # fields = nmeastr.split(',')
        # str_time = fields[4] + '-' + fields[3] + '-' + fields[2] + ' ' + fields[1][:2] + ':' + \
        #            fields[1][2:4] + ':' + fields[1][4:]
        ctx['date'] = fields[4] + '-' + fields[3] + '-' + fields[2]
        # print(ctx['date'])
        # dtime = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")

    elif nmeastr.startswith('$GNRMC') or nmeastr.startswith('$GPRMC'):
        if ctx.get('disable_nmea'):
            return
        # print(nmeastr)
        r = dict()
        r['type'] = 'gps'
        r['sensor'] = 'm8n'
        # fields = nmeastr.split(',')

        if fields[7] == '':
            # print('no thanks')
            return
        # try:
        r['pos_type'] = fields[2]
        r['speed'] = 0.514444 * float(fields[7]) if fields[7] else None  # m/s
        r['speed'] = 3.6 * r['speed']  # km/h
        r['lat'] = float(fields[3][:2]) + float(fields[3][2:]) / 60 if fields[3] else None
        r['lon'] = float(fields[5][:3]) + float(fields[5][3:]) / 60 if fields[5] else None
        r['heading'] = float(fields[8]) if fields[8] else None
        # print(fields)
        str_time = '20' + fields[9][4:] + '-' + fields[9][2:4] + '-' + fields[9][0:2] + ' ' + fields[1][:2] + ':' + \
                   fields[1][2:4] + ':' + fields[1][4:]
        dtime = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")
        dtime = dtime + datetime.timedelta(hours=8)
        if ctx:
            ctx['date'] = '20' + fields[9][4:] + '-' + fields[9][2:4] + '-' + fields[9][0:2]
        # print(dtime)
        r['ts'] = dtime.timestamp()
        # print(dtime.timestamp())
        # except Exception as e:
        #     print(e, fields)
        #     return

        # fileHandler.insert_raw((time.time(), 'gps-speed', str(r['speed'])))
        # print('speed', r['speed'])
        # print(fields)

        return r
    elif nmeastr.startswith('$PASHR'):
        # print(nmeastr)
        r = dict()
        r['type'] = 'pashr'
        data = nmeastr.split('*')[0]
        # fields = data.split(',')

        if len(fields) < 11:
            print(nmeastr)
            return
        if len(fields) > 11:
            r['ins_status'] = fields[11]

        if ctx and ctx.get('date'):
            str_time = ctx['date'] + ' ' + fields[1][:2] + ':' + fields[1][2:4] + ':' + fields[1][4:]
            dtime = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")
            dtime = dtime + datetime.timedelta(hours=8)
            r['ts'] = dtime.timestamp()
            # print(r['ts'])
        else:
            # str_time = '2020-11-10' + ' ' + fields[1][:2] + ':' + fields[1][2:4] + ':' + fields[1][4:]
            # dtime = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")
            # dtime = dtime + datetime.timedelta(hours=8)
            # r['ts'] = dtime.timestamp()
            # pass
            return

        states = ['NONE', 'SINGLE', 'NARROW_INT']

        r['yaw'] = float(fields[2])
        r['roll'] = float(fields[4])
        r['pitch'] = float(fields[5])
        r['undulation'] = float(fields[6])
        r['roll_sgm'] = float(fields[7])
        r['pitch_sgm'] = float(fields[8])
        r['yaw_sgm'] = float(fields[9])
        r['pos_type'] = states[int(fields[10])]

        return r

    elif nmeastr.startswith('$PBSOL'):
        # print(nmeastr)
        bds_offset = 18.0
        r = dict()
        r['type'] = 'inspva'
        year = int(fields[2])
        month = int(fields[3])
        day = int(fields[4])
        hour = int(fields[5])
        minutes = int(fields[6])
        ms = int(fields[7])
        r['sensor_time'] = int(fields[8])  # in ms
        week = int(fields[9])
        tow = int(fields[10])

        r['ts'] = week * 604800 + tow / 1000.0 + 315964800.0 - bds_offset
        navmode = int(fields[11])
        if not navmode:
            r['pos_type'] = 'NONE'
        elif navmode & (1 << 2):
            r['pos_type'] = 'INS'
        elif navmode & (1 << 1):
            if navmode & (1 << 12):
                r['pos_type'] = 'PSRDIFF'
            elif navmode & (1 << 13):
                r['pos_type'] = 'NARROW_INT'
            elif navmode & (1 << 14):
                r['pos_type'] = 'NARROW_FLOAT'
            elif navmode & (1 << 15):
                r['pos_type'] = 'PPP'
        elif navmode & (1 << 3):
            if navmode & (1 << 12):
                r['pos_type'] = 'INS_PSRDIFF'
            elif navmode & (1 << 13):
                r['pos_type'] = 'INS_RTKFIXED'
            elif navmode & (1 << 14):
                r['pos_type'] = 'INS_RTKFLOAT'
            elif navmode & (1 << 15):
                r['pos_type'] = 'PPP'
        else:
            r['pos_type'] = navmode
        r['lat'] = float(fields[12])
        r['lon'] = float(fields[13])
        r['hgt_eps'] = float(fields[14])
        r['hgt'] = float(fields[15])
        r['vel_n'] = float(fields[16]) / 100.0
        r['vel_e'] = float(fields[17]) / 100.0
        r['vel_u'] = -float(fields[18]) / 100.0
        r['trk_gnd'] = float(fields[19]) / 100.0
        r['travel'] = float(fields[20]) / 100.0
        r['roll'] = float(fields[21]) / 100.0
        r['pitch'] = float(fields[22]) / 100.0
        r['yaw'] = float(fields[23]) / 100.0
        r['rsv1'] = int(fields[24])
        r['rsv2'] = int(fields[25])
        r['lon_sgm'] = float(fields[26]) / 100.0
        r['lat_sgm'] = float(fields[27]) / 100.0
        r['hgt_sgm'] = float(fields[28]) / 100.0
        r['vel_n_sgm'] = float(fields[29]) / 100.0
        r['vel_e_sgm'] = float(fields[30]) / 100.0
        r['vel_u_sgm'] = float(fields[31]) / 100.0
        r['roll_sgm'] = float(fields[32]) / 100.0
        r['pitch_sgm'] = float(fields[33]) / 100.0
        r['yaw_sgm'] = float(fields[34]) / 100.0
        r['misal_roll'] = float(fields[35]) / 100.0
        r['misal_pitch'] = float(fields[36]) / 100.0
        r['misal_yaw'] = float(fields[37]) / 100.0
        r['station_id'] = int(fields[38])
        r['diff_age'] = int(fields[39])
        r['heading_valid'] = int(fields[40])
        # r['rbv_roll'] = float(fields[41]) / 100.0
        # r['rbv_pitch'] = float(fields[42]) / 100.0
        # r['rbv_yaw'] = float(fields[43]) / 100.0
        ctx['disable_nmea'] = True

        return r

