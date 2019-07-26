import datetime
import time


def decode_nmea(nmeastr):
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
        r['type'] = 'vehicle_state'
        r['sensor'] = 'm8n'
        fields = nmeastr.split(',')
        if fields[7] == '':
            # print('no thanks')
            return
        # try:
        r['speed'] = 0.514444 * float(fields[7]) if fields[7] else None  # m/s
        r['speed'] = 3.6 * r['speed']  # km/h
        r['lat'] = float(fields[3]) / 100.0 if fields[3] else None
        r['lon'] = float(fields[5]) / 100.0 if fields[5] else None
        r['heading'] = float(fields[8]) if fields[8] else None
        # print(fields)
        str_time = '20' + fields[9][4:] + '-' + fields[9][2:4] + '-' + fields[9][0:2] + ' ' + fields[1][:2] + ':' + \
                   fields[1][2:4] + ':' + fields[1][4:]
        dtime = datetime.datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f")
        dtime = dtime + datetime.timedelta(hours=8)
        # print(dtime)
        r['ts_origin'] = time.mktime(dtime.timetuple())

        # except Exception as e:
        #     print(e, fields)
        #     return

        # fileHandler.insert_raw((time.time(), 'gps-speed', str(r['speed'])))
        # print('speed', r['speed'])
        # print(fields)
        return r


def parse_ublox(protocol, data, ctx=None):
    if protocol == 'NMEA':
        r = decode_nmea(data)
        if r and len(r) > 0:
            return r

    elif protocol == 'ubx':
        pass

    elif protocol == 'rtcm':
        pass
