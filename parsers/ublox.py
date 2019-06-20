def decode_nmea(nmeastr):
    # print(msg)

    if not nmeastr[0] == '$':
        # print('not $')
        # print(nmeastr)
        return
    else:
        # print('nmea msg')
        pass

    if nmeastr.startswith('$GNRMC') or nmeastr.startswith('$GPRMC'):
        r = dict()
        r['type'] = 'vehicle_state'
        fields = nmeastr.split(',')
        if fields[7] == '':
            return
        try:
            r['speed'] = 0.514444 * float(fields[7])  # m/s
            r['lat'] = float(fields[3]) / 100.0
            r['lon'] = float(fields[5]) / 100.0
            r['heading'] = float(fields[8])

        except Exception as e:
            # print(e, fields)
            return

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
