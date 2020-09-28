import datetime
import time


def decode_nmea(nmeastr, ctx=None):
    # sample: $GNRMC,021346.50,A,2232.42074,N,11356.84392,E,0.123,,200719,,,D*61
    # print(msg)
    if not nmeastr[0] == '$':
        # print('not $')
        # print(nmeastr)
        return
    else:
        # print('nmea msg')
        pass

    if nmeastr.startswith('$GNRMC') or nmeastr.startswith('$GPRMC'):
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
        r = dict()
        r['type'] = 'pashr'
        data = nmeastr.split('*')[0]
        fields = data.split(',')

        if len(fields) < 11:
            return
        if len(fields) > 11:
            r['ins_status'] = fields[11]

        if ctx and ctx.get('date'):
            str_time = ctx['date'] + ' ' + fields[1][:2] + ':' + fields[1][2:4] + ':' + fields[1][4:]
            dtime = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")
            dtime = dtime + datetime.timedelta(hours=8)
            r['ts'] = dtime.timestamp()
        else:
            return

        states = ['NONE', 'SINGLE', 'RTK_FIX']

        r['yaw'] = float(fields[2])
        r['roll'] = float(fields[4])
        r['pitch'] = float(fields[5])
        r['undulation'] = float(fields[6])
        r['roll_sgm'] = float(fields[7])
        r['pitch_sgm'] = float(fields[8])
        r['yaw_sgm'] = float(fields[9])
        r['pos_type'] = states[int(fields[10])]


def parse_ublox(data, ctx=None):
    r = decode_nmea(data, ctx=ctx)
    if r and len(r) > 0:
        return r
