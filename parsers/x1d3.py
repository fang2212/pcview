import cantools

db = cantools.database.load_file('dbc/X1D3_guojian_20200414.dbc', strict=False)


def parse_x1d3_simple(id, buf, ctx=None):
    ids = [m.frame_id for m in db.messages]
    if id not in ids:
        return None
    r = db.decode_message(id, buf)
    # print('0x{:x}'.format(id), r)
    ret = None
    if id == 0x10f007e8:  # LDW
        ret = r
        ret['type'] = 'ldw'

    elif id == 0x10fe6fe8:  # FCW
        ret = r
        ret['type'] = 'fcw'

    if ret:
        print(ret)
    return ret


def parse_x1d3(can_id, can_data, ctx={}):
    ret = {}
    # can_data = b''.join([x.to_bytes(1, 'little') for x in can_data])

    # if can_id == 0x10FE6FE8 and ctx.get("x1d3_can_protocol") != "guojian":
    #     if ctx.get("x1d3_can_protocol", "ttc") == "ttc":
    #         suf = bin(can_data[2])[2:]
    #         suf = suf if len(suf) >= 8 else '0' * (8 - len(suf)) + suf
    #         pre = bin(can_data[3])[2:]
    #         pre = pre if len(pre) >= 8 else '0' * (8 - len(pre)) + pre
    #         v = pre[-4:] + suf
    #         dis = int(v, 2) * 0.0625
    #
    #         suf = bin(can_data[0])[2:]
    #         suf = suf if len(suf) >= 8 else '0' * (8 - len(suf)) + suf
    #         pre = bin(can_data[1])[2:]
    #         pre = pre if len(pre) >= 8 else '0' * (8 - len(pre)) + pre
    #
    #         v = pre[-2:] + suf
    #         ttc = int(v, 2) * 0.01
    #
    #         ret["x1d3_ttc"] = ttc
    #         ret['x1d3_dis'] = dis
    #
    #     else:
    #         suf = bin(can_data[1])[2:]
    #         suf = suf if len(suf) >= 8 else '0' * (8 - len(suf)) + suf
    #         dis = int(suf, 2)
    #
    #         suf = bin(can_data[0])[2:]
    #         suf = suf if len(suf) >= 8 else '0' * (8 - len(suf)) + suf
    #         sp = int(suf, 2)
    #
    #         ret['x1d3_dis'] = dis
    #         ret['x1d3_vx'] = sp

    # r = {'type': 'warning'}
    if can_id in [m.frame_id for m in db.messages]:
        r = db.decode_message(can_id, can_data)
    else:
        return

    if 'LaneDepartureLeft' in r:
        if r["LaneDepartureLeft"] == "warning":
            lldw = 1
        else:
            lldw = 0

        ret['ldw_left'] = lldw

        if r["LaneDepartureRight"] == "warning":
            rldw = 1
        else:
            rldw = 0

        ret['ldw_right'] = rldw

    if 'ForwardCollisionWarning' in r:
        if r["ForwardCollisionWarning"] == "Level 1 warning":
            fcw = 1
        elif r["ForwardCollisionWarning"] == "Level 2 warning":
            fcw = 2
        else:
            fcw = 0
        ret['fcw_level'] = fcw

    if 'SteeringWheelAngle' in r:
        ret['steer_angle'] = r['SteeringWheelAngle']
    if 'CurrentGear' in r:
        ret['gear'] = r['CurrentGear']

    if 'TurnSignalSwitch' in r:
        turn = r['TurnSignalSwitch']
        if 'Left' in turn:
            ret['turn'] = "left"
        elif 'Right' in turn:
            ret['turn'] = "right"
        else:
            ret['turn'] = "no"

    if 'BrakeSwitch' in r:
        brake = r['BrakeSwitch']
        if "depressed" in brake:
            ret['brake'] = "1"
        elif "released" in brake:
            ret['brake'] = "0"
        else:
            ret['brake'] = "-1"

    if 'FrontOperatorWiperSwitch' in r:
        ret['wiper'] = r['FrontOperatorWiperSwitch']

    if 'DistanceToForwardVehicle' in r:
        ret['pos_lon'] = r['DistanceToForwardVehicle']

    if 'SpeedOfForwardVehicle' in r:
        ret['vel_lon'] = r['SpeedOfForwardVehicle']

    if ret:
        ret['type'] = 'warning'
        return ret

