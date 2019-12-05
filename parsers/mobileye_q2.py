def parse_mobileye(id, buf):
    if id not in [0x700, 0x760, 0x727]:
        return None
    # print('0x %x' % id)
    result = {}
    if id == 0x760:
        speed = buf[2]
        # print("vehicle speed:", speed)
        return {'type': 'vehicle_state', 'speed': speed}

    if id == 0x737:

        result['lane_curv'] = buf[0] | buf[1] << 8
        result['lane_heading'] = buf[2] | (buf[3] & 0x0f) << 8
        result['ca'] = (buf[3] & 0x10) >> 4
        result['rldw_en'] = (buf[3] & 0x20) >> 5
        result['lldw_en'] = (buf[3] & 0x40) >> 6
        result['na'] = (buf[3] & 0x80) >> 7
        result['yaw_angle'] = buf[4] | buf[5] << 8
        result['pitch_angle'] = buf[6] | buf[7] << 8

        # print("0x737 mb lane")

    if id == 0x738:

        result['n_obstacles'] = buf[0]
        result['timestamp'] = buf[1]
        result['app_ver'] = buf[2]

        print("0x738 #obs q2:{}".format(result['n_obstacles']))

    result['type'] = 'mbq2'

    return result