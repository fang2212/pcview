import cantools

db_x1l = cantools.database.load_file('dbc/liuqi_960p_20191030.dbc', strict=False)


# x1l_obs = []
def parse_x1l(id, buf, ctx=None):
    # global x1l_obs
    if id == 0x10f007e8:
        r = db_x1l.decode_message(id, buf, decode_choices = False)
        fcw_level = r.get('FCW_warning_level')
        ldw_left = r.get('lane_departure_imminent_left')
        ldw_right = r.get('lane_departure_imminent_right')
        x = r.get('Target_Vehicle_PosX')
        ttc = r.get('CAN_VIS_OBS_TTC_WITH_ACC')

        ret = {'type': 'warning', 'sensor': 'x1l',  'class': 'object', "width": 1.5, 'cipo': True,
               'id': 'x1l_warn', 'pos_lon': x, 'TTC': ttc, 'ldw_left': ldw_left, 'ldw_right': ldw_right, 'fcw_level': fcw_level}
        # x1l_obs.append(ret)
        # print(ret)
        return ret
