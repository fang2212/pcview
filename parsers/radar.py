import cantools
from tools.transform import *
from tools.match import *

# M_PI = 3.141592653589793238462643383279503

db_esr = cantools.database.load_file('dbc/ESR DV3_64Tgt.dbc', strict=False)
db_ars = None
# db_huayu = cantools.database.load_file('/home/nan/workshop/doc/华域/lrr10_1.dbc', strict=False)

db_mrr = cantools.database.load_file('dbc/bosch_mrr_output.dbc', strict=False)
db_lmr = cantools.database.load_file('dbc/HETLMR.dbc', strict=False)
db_hmb = cantools.database.load_file('dbc/szhmb.dbc', strict=False)


def parse_ars(id, buf):
    result = {}
    if id == 0x600:
        result['type'] = 'cluster_info'
        result['n_targets_near'] = buf[0]
        result['n_targets_far'] = buf[1]
        result['meas_cnt'] = buf[2] << 8 | buf[3]
        result['if_ver'] = buf[4] >> 4

    if id == 0x701:
        result['type'] = 'cluster_general'
        result['dist_lon'] = 0.2 * (buf[1] << 5 | buf[2] >> 3) - 500.0
        result['dist_lat'] = 0.2 * ((buf[2] & 0x03) << 8 | buf[3]) - 102.3
        result['vrel_lon'] = 0.25 * (buf[4] << 2 | buf[5] >> 6) - 128.0
        result['vrel_lat'] = 0.25 * ((buf[5] & 0x3f) << 3 | buf[6] >> 5) - 64.0
        result['dyn_prop'] = buf[6] & 0x07
        result['rcs'] = 0.5 * buf[7] - 64.0

    if id == 0x60A:
        result['type'] = 'obj_info'
        result['n_objs'] = buf[0]
        result['meas_cnt'] = buf[1] << 8 | buf[2]
        result['if_ver'] = buf[3] >> 4

    if id == 0x60B:
        result['type'] = 'obj_general'
        result['id'] = buf[0]
        result['dist_lon'] = 0.2 * (buf[1] << 5 | buf[2] >> 3) - 500.0
        result['dist_lat'] = 0.2 * ((buf[2] & 0x07) << 8 | buf[3]) - 204.6
        result['vrel_lon'] = 0.25 * (buf[4] << 2 | buf[5] >> 6) - 128.0
        result['vrel_lat'] = 0.25 * ((buf[5] & 0x3F) << 3 | buf[6] >> 5) - 64.0
        result['dyn_prop'] = buf[6] & 0x07
        result['rcs'] = 0.5 * buf[7] - 64.0

    return result


esr_filter = CIPOFilter()
esrobs = []


def parse_esr(id, buf):
    global esrobs
    ids = [m.frame_id for m in db_esr.messages]
    if id not in ids:
        return None
    r = db_esr.decode_message(id, buf)
    # print('0x%x' % id)
    tgt_status = r.get('CAN_TX_TRACK_STATUS')
    if tgt_status is not None:
        if tgt_status == 'Updated_Target' or tgt_status == 'Coasted_Target' \
                or tgt_status == 'New_Target' or tgt_status == 'New_Updated_Target':
            range = r.get('CAN_TX_TRACK_RANGE')
            angle = r.get('CAN_TX_TRACK_ANGLE')
            tid = id - 0x500
            # x = cos(angle * pi / 180.0) * range + 1.64
            # y = sin(angle * pi / 180.0) * range - 0.4
            x, y = trans_polar2rcs(angle, range, install['esr'])
            # print('ESR 0x%x' % id, r)
            ret = {'type': 'obstacle', 'id': tid, 'pos_lon': x, 'pos_lat': y, 'color': 1}
            esrobs.append(ret)
            # if esr_filter.update(ret):
            #     ret['cipo'] = True
            # return ret
        else:
            # print('ESR 0x%x' % id, r)
            pass
    elif 'CAN_TX_MAXIMUM_TRACKS_ACK' in r:
        # print(r['CAN_TX_MAXIMUM_TRACKS_ACK'])
        pass
    elif id == 0x540:
        idx = r['CAN_TX_TRACK_CAN_ID_GROUP']
        if idx == 0:
            ret = esr_filter.add_cipo(esrobs)
            esrobs = []
            return ret
    elif id == 0x4e3:
        # print('0x%x' % id)
        print('0x%x' % id, r)


def parse_bosch_mrr(id, buf):
    ids = [m.frame_id for m in db_mrr.messages]
    if id not in ids:
        return None
    if 0x660 <= id <= 0x67f:
        idx = id - 0x660

        r = db_mrr.decode_message(id, buf)
        oid = r['X_Object{:02d}_ID'.format(idx)]
        x = r['X_Object{:02d}_dx'.format(idx)]
        y = -r['X_Object{:02d}_dy'.format(idx)]
        idx = id - 0x660
        if r['X_Object%02d_wExist' % idx] > 0.0:
            # print('0x%x' % id, r)
            return {'type': 'obstacle', 'id': oid, 'pos_lon': x, 'pos_lat': y, 'color': 1}
    elif id == 0x680:
        r = db_mrr.decode_message(id, buf)
        # print('0x%x' % id, r)
        pass

    return None


def parse_hawkeye_lmr(id, buf):
    ids = [m.frame_id for m in db_lmr.messages]
    if id not in ids:
        return None
    r = db_lmr.decode_message(id, buf)
    # print('0x%x' % id, r)
    if 'CANTX_TargetSNR' in r:
        if r['CANTX_TargetSNR'] > 0:
            # print('0x%x' % id, r)
            range = r.get('CANTX_TragetRange')
            angle = r.get('CANTX_TargetAzimuth')
            # x = cos(angle * pi / 180.0) * range
            # y = sin(angle * pi / 180.0) * range
            x, y = trans_polar2rcs(angle, range, install['lmr'])
            return {'type': 'obstacle', 'id': id - 0x500, 'pos_lon': x, 'pos_lat': y, 'color': 1}

    return None


def parse_hmb(id, buf):
    # print('0x%x' % id)
    ids = [m.frame_id for m in db_hmb.messages]
    if id not in ids:
        return None

    r = db_hmb.decode_message(id, buf)

    # if r['Range'] :
    #     return

    range = r.get('Range')
    angle = -r.get('Angle')
    # x = cos(angle * pi / 180.0) * range
    # y = sin(angle * pi / 180.0) * range
    x, y = trans_polar2rcs(angle, range, install['hmb'])

    # print("hmb radar frame")
    result = {'type': 'obstacle', 'id': id - 0x500, 'pos_lon': x, 'pos_lat': y, 'color': 4}
    print(result)
    return result
