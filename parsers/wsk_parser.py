import cantools

db_unop_mrr = cantools.database.load_file('dbc/Communication_ Matrix_V0.7[20210621] - object.dbc', strict=False)
db_cubtek_mrr = cantools.database.load_file('dbc/Cubtek_front radar CAN protocol.dbc', strict=False)


# 为升科前雷达
def parse_wsk_mrr(id, buf, ctx=None):
    ids = [m.frame_id for m in db_cubtek_mrr.messages]
    if id not in ids:
        return None

    if ctx.get("obs_list") is None:
        ctx["obs_list"] = []

    r = db_cubtek_mrr.decode_message(id, buf, decode_choices=False)
    if id == 0x300:
        if(len(ctx["obs_list"])> 0):
            ret = ctx["obs_list"].copy()
            ctx["obs_list"].clear()
            return ret

        return {
            'type': 'obstacle',
            "sensor": "wsk",
            'steer_angle': r.get('Str_Angle'),
            'speed': r.get('VehSpeed')/3.6,
            'yaw_rate': -r.get('YawRate'),
            'id': 0,
            'pos_lon': 0,
            'pos_lat': 0,
            'range': 0,
            'angle': 0,
            'range_rate': 0,
        }
    if 0x503 <= id <= 0x552:
        obj_idx = (id - 0x501) / 2
        if id % 2:
            ret = {
                'type': 'obstacle',
                "sensor": "wsk",
                'id': r['RadarObj%d_ID_A' % (obj_idx)],
                'pos_lon': r['RadarObj%d_Pos_X' % (obj_idx)],
                'pos_lat': -r['RadarObj%d_Pos_Y' % (obj_idx)],
                'v_lon': r['RadarObj%d_Vel_X' % (obj_idx)],
                'v_lat': -r['RadarObj%d_Vel_Y' % (obj_idx)],
                'range_rate':  r['RadarObj%d_Vel_X' % (obj_idx)]
            }
            ctx["obs_list"].append(ret)
        else:
            for obs in ctx["obs_list"]:
                if obs['id'] == r['RadarObj%d_ID_B' % (obj_idx)]:
                    obs['dyn_prop'] = 'dyn_prop_%03d' % (r['RadarObj%d_DynProp' % (obj_idx)])
                    obs['tgt_status'] = 'State_%07f' % (r['RadarObj%d_ProbOfExist' % (obj_idx)])
                    break


# # 20211202联合光电
def parse_unop_mrr(id, buf, ctx=None):
    ids = [m.frame_id for m in db_unop_mrr.messages]
    if id not in ids:
        return None

    r = db_unop_mrr.decode_message(id, buf)

    if ctx.get("obs_list") is None:
        ctx["obs_list"] = []
        ctx['cnt_unop'] = 300

    global unopobs,meas_cnt_unop
    if id == 0x630:
        ctx['cnt_unop'] = r.get('Object_Num')
        if len(ctx["obs_list"]) > 0:
            ret = ctx["obs_list"].copy()
            ctx["obs_list"].clear()
            return ret

        return {
            'speed':r.get('Vehicle_Speed'),
            'yaw_rate':r.get('Vehicle_YawRate'),
            'type': 'obstacle',
            'id': 0,
            'pos_lon': 0,
            'pos_lat': 0,
            'range': 0,
            'angle': 0,
            'range_rate': 0,
            }
    if id == 0x631:
        tid = r.get('Object_Index')
        range_lon = r.get('Object_y')
        range_lat = r.get('Object_x')
        v_lon = r.get('Object_vy')
        v_lat = r.get('Object_vx')
        if abs(v_lon)>0:
            vr=((v_lon**2+v_lat**2)**0.5)*v_lon/abs(v_lon)
        else:
            vr = ((v_lon ** 2 + v_lat ** 2) ** 0.5)
        # range,angle = trans_rcs2polar(range_lon, range_lat)#方位角
        ret = {
            'type': 'obstacle',
            'id': tid,
            'pos_lon': range_lon,
            'pos_lat': range_lat,
            'range_rate': vr,
            'v_lon':v_lon,
            'v_lat':v_lat,
            }
        ctx["obs_list"].append(ret)
    # if id == 0x632:
    #     tid = r.get('Object_Index')
    #     dyn_prop = r.get('Object_Dynamic')
    #     rcs = r.get('Object_RCS')
    #     i = 0
    #     for obs in ctx["obs_list"]:
    #         if obs['id'] == tid:
    #             # unopobs[i]['tgt_status']=(MeasState*(1000000000)+ProbOfExist*(100000000))
    #             obs['dyn_prop'] = 'dyn_prop_' + str(dyn_prop)
    #             obs['power'] = rcs
    #             break
    if id == 0x633:
        tid = r.get('Object_Index')
        ObjLength = r.get('Object_Length')
        ObjWidth = r.get('Object_Wide')
        ObjOrientationAngel = r.get('Object_hight')
        ObjClass = r.get('Object_Class')
        for obs in ctx['obs_list']:
            if obs['id'] == tid:
                obs['ObjLength']=ObjLength
                obs['ObjWidth'] = ObjWidth
                obs['ObjOrientationAngel'] = ObjOrientationAngel
                obs['ObjClass'] = ObjClass
                break
        if ctx['cnt_unop'] <= len(ctx['obs_list']):
            ret = ctx['obs_list'].copy()
            ctx['obs_list'].clear()
            return ret
    return None
