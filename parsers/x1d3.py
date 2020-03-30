import cantools

db_x1d3 = cantools.database.load_file('dbc/X1D3_guojian_20200313.dbc', strict=False)


def parse_x1d3(id, buf, ctx=None):
    ids = [m.frame_id for m in db_x1d3.messages]
    if id not in ids:
        return None
    r = db_x1d3.decode_message(id, buf)
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


