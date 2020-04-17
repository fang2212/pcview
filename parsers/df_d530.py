import cantools

db_dfd530 = cantools.database.load_file('dbc/1242_Guojian.dbc', strict=False)


def parse_dfd530(id, buf, ctx=None):
    ids = [m.frame_id for m in db_dfd530.messages]
    if id not in ids:
        # print('id not in dbc: 0x{:x}'.format(id))
        return
    try:
        r = db_dfd530.decode_message(id, buf)
    except Exception as e:
        return

    if not r:
        return
    # print('0x{:x}'.format(id), r)
    obj = None
    if id == 0xcf02fe8:
        obj = {'type': 'control', 'class': 'aeb_warn', 'sensor': 'd530'}
        obj['aeb_level'] = r['AEB1_ColWrnLevel']

    elif id == 0xc040bfe:
        obj = {'type': 'control', 'class': 'xbr', 'sensor': 'd530'}
        obj['xbr_acc'] = r['XBR_ExtlAccelerationDemand']
    elif id == 0x18febf0b:
        obj = {'type': 'vehicle_state', 'sensor': 'd530', 'speed': r['EBC2_FrontAxleSpeed']}

    if obj:
        return obj