import datetime


pos_types = {0: 'NONE', 1: 'SINGLE', 2: 'INS_PSRDIFF', 4: 'INS_RTKFIXED', 5:'INS_RTKFLOAT', 6: 'INS', 7: 'FIXEDPOS'}


def parse_pim222(msg_type, msg, ctx=None):
    if isinstance(msg, bytes):
        nmeastr = msg.decode()
    else:
        nmeastr = msg

    if nmeastr.startswith('$GNGGA') or nmeastr.startswith('$GPGGA'):
        r = dict()
        # print(nmeastr)
        r['type'] = 'gpgga'
        fields = nmeastr.split(',')
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
        fields = nmeastr.split(',')
        # str_time = fields[4] + '-' + fields[3] + '-' + fields[2] + ' ' + fields[1][:2] + ':' + \
        #            fields[1][2:4] + ':' + fields[1][4:]
        ctx['date'] = fields[4] + '-' + fields[3] + '-' + fields[2]
        # print(ctx['date'])
        # dtime = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")


    elif nmeastr.startswith('$GNRMC') or nmeastr.startswith('$GPRMC'):
        # print(nmeastr)
        r = dict()
        r['type'] = 'gps'
        r['sensor'] = 'm8n'
        fields = nmeastr.split(',')

        if fields[7] == '':
            # print('no thanks')
            return
        # try:
        r['pos_type'] = fields[2]
        r['speed'] = 0.514444 * float(fields[7]) if fields[7] else None  # m/s
        r['speed'] = 3.6 * r['speed']  # km/h
        r['lat'] = float(fields[3][:2]) + float(fields[3][2:])/60 if fields[3] else None
        r['lon'] = float(fields[5][:3]) + float(fields[5][3:])/60 if fields[5] else None
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
        fields = data.split(',')

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