import os
import json
import struct
import time

from parsers.decode_eyeq4_100 import decode_obs, decode_lane_marker, decode_speed


def cal_type_sz_signed(type_str) -> (int, int, bool):
    if type_str in ['double', 'float64', 'float64_t', 'real64_t']:
        return 2, 8, False

    if type_str in ['single', 'float', 'float32', 'float32_t', 'real32_t']:
        return 1, 4, False

    if type_str in ['uint8', 'uint8_t', 'unsigned char', 'bool', 'boolean', 'boolean_t', 'unsigned8_t']:
        return 0, 1, False

    if type_str in ['int8', 'sint8', 'int8_t', 'sint8_t', 'signed char', 'char', 'signed8_t']:
        return 0, 1, True

    if type_str in ['uint16', 'uint16_t', 'unsigned short', 'unsigned16_t', 'bitfield16_t']:
        return 0, 2, False

    if type_str in ['int16', 'sint16', 'int16_t', 'sint16_t', 'signed short', 'short', 'signed16_t']:
        return 0, 2, True

    if type_str in ['uint32', 'uint32_t', 'unsigned int', 'unsigned32_t', 'bitfield32_t']:
        return 0, 4, False

    if type_str in ['int32', 'sint32', 'int32_t', 'sint32_t', 'signed int', 'int', 'signed32_t']:
        return 0, 4, True

    if type_str in ['uint64', 'uint64_t', 'unsigned64_t']:
        return 0, 8, False

    if type_str in ['int64', 'sint64', 'int64_t', 'sint64_t', 'signed64_t']:
        return 0, 8, True

    return 0, 0, 0


def read_vis_definiaton(def_src_num_ver_file):
    with open(def_src_num_ver_file, "r") as rf:

        expected_bytes = int(rf.readline().strip())
        offset = 0
        repeat = 0
        repeat_buf = []
        current_level = 0
        key_data = {}
        for line in rf:
            line = line.strip()
            if line == "":
                continue

            if "REPEAT" == line[:6]:
                repeat = int(line[6:])
                current_level += 1
                repeat_buf.append([repeat, []])
                continue

            if "END_REPEAT" == line:
                current_level -= 1
                repeat, data = repeat_buf[-1]
                last_len = len(data)
                data = data * repeat
                for i in range(0, last_len * repeat):
                    data[i] = data[i] + "." + str(i // last_len)

                repeat_buf.pop(-1)
                if current_level:
                    repeat_buf[-1][1].extend(data)
                else:
                    for d in data:
                        fields = d.split()
                        tp, sz, sig = cal_type_sz_signed(fields[0])
                        if sz == 0:
                            continue
                        item = {
                            "signal": fields[-1],
                            "type": tp,
                            "size": sz,
                            "signed": sig,
                            "offset": offset
                        }
                        offset += sz
                        key_data[fields[-1]] = item
                    continue

            padd = 0
            if "PADDING" == line[:7]:
                padd = int(line[7:])

            if current_level:
                if "PADDING" == line[:7]:
                    repeat_buf[-1][1].extend(["uint8 padd"] * padd)
                else:
                    repeat_buf[-1][1].append(line)

            else:

                if "PADDING" == line[:7]:
                    offset += padd
                else:
                    fields = line.split()
                    tp, sz, sig = cal_type_sz_signed(fields[0])
                    if sz == 0:
                        continue
                    item = {
                        "signal": fields[-1],
                        "type": tp,
                        "size": sz,
                        "signed": sig,
                        "offset": offset
                    }
                    offset += sz
                    key_data[fields[-1]] = item
        if not os.path.exists("./str_005_016.json"):
            wf = open("./str_005_016.json", "w")
            print(json.dumps(key_data, indent=2), file=wf)
            wf.close()
    return key_data


def decode_header(head: bytes) -> dict:
    res = {
        'versionInfo': int.from_bytes(head[8:10], signed=False, byteorder="little"),
        'sourceInfo': head[16],
        'sensorId': head[31],
        'streamNumber': head[27],
        'streamVersion': head[28],
        'streamDataLen': 1,
        'streamChunks': head[29],
        'cTime': int.from_bytes(head[4:8], byteorder="little", signed=False),
        'pcTime': int.from_bytes(head[0:4], byteorder="little", signed=False),
        'sourceTxCnt': int.from_bytes(head[10:12], signed=False, byteorder="little"),
        'sourceTxTime': int.from_bytes(head[12:16], signed=False, byteorder="little"),
        'streamRefIndex': int.from_bytes(head[20:24], signed=False, byteorder="little"),
        'streamTxCnt': head[26],
        'streamChunkIdx': head[30],
        'streamChunkLen': int.from_bytes(head[24:26], byteorder="little", signed=False),
        # 'payloadStartFilePosition', payloadFilePosition);
    }
    return res


def decode_data(data: bytes, stream_info):

    lane_res = decode_lane_marker(stream_info, data)
    obs_res = decode_obs(stream_info, data)

    # hpp_res = decode_hpp(stream_info, data)
    # traffic_sign_res = decode_traffic_sign(stream_info, data)
    #
    # reflect_sign_res = decode_reflect_sign(stream_info, data)
    # road_arrow_res = decode_road_arrow(stream_info, data)
    # road_border_res = decode_road_border(stream_info, data)
    # road_cross_res = decode_road_cross(stream_info, data)
    # road_speedlimit_res = decode_road_speedlimit(stream_info, data)
    # road_transition_res = decode_road_transition(stream_info, data)
    # stopline_res = decode_stop_line(stream_info, data)

    return lane_res, obs_res


stream_info_005_016 = read_vis_definiaton("./dbc/strdef_src022_str005_ver016_Vis.txt")
stream_info_007_012 = read_vis_definiaton("./dbc/strdef_src022_str007_ver012.txt")


def parser_q4_100(id, buf, ctx={}):

    # str_005_016.update({'streamNumber': 5, 'streamVersion': 16, "streamChunkLen": 6192})

    if len(buf) < 32:
        return None

    header_info = decode_header(buf[:32])

    # only decode strdef_src022_ver016_vis.txt
    if header_info["streamNumber"] == 5 and header_info["streamVersion"] == 16 and header_info["streamChunkLen"] == 6192 and len(buf)-32 == 6192:
        lane, obs = decode_data(buf[32:], stream_info_005_016)
        lane.extend(obs)
        return lane
    elif header_info["streamNumber"] == 7 and header_info["streamVersion"] == 12 and header_info["streamChunkLen"] == 212 and len(buf)-32 == 212:
        r = decode_speed(stream_info_007_012, buf[32:])
        return r

import cantools
from cantools import database
db_rt = cantools.database.load_file('dbc/RT-Range_User.dbc', strict=False)

db_arc_soft1 = cantools.database.load_file('/home/fyq/Desktop/pcview/q4_data/dbc/arc_soft/ArcSoft_Objects_List.dbc',strict=False)
db_arc_soft2 = cantools.database.load_file('/home/fyq/Desktop/pcview/q4_data/dbc/arc_soft/ArcSoft_Lane_List.dbc',strict=False)

db_RT_can1 = cantools.database.load_file('/home/fyq/Desktop/pcview/q4_data/dbc/RT_DBC/Hunter.dbc', strict=False)
db_RT_can2 = cantools.database.load_file('/home/fyq/Desktop/pcview/q4_data/dbc/RT_DBC/RTrange.dbc', strict=False)
db_RT_can3 = cantools.database.load_file('/home/fyq/Desktop/pcview/q4_data/dbc/RT_DBC/Target1.dbc', strict=False)
db_RT_can4 = cantools.database.load_file('/home/fyq/Desktop/pcview/q4_data/dbc/RT_DBC/Lane.dbc', strict=False)
db_RT_can5 = cantools.database.load_file('/home/fyq/Desktop/pcview/q4_data/dbc/RT_DBC/Lane_status.dbc', strict=False)

db_pb_can = cantools.database.load_file('/home/fyq/Desktop/pcview/q4_data/dbc/MY20_PB_V20.20.dbc', strict=False)
db_ce_can = cantools.database.load_file('/home/fyq/Desktop/pcview/q4_data/dbc/MY20_CB_V20.20.dbc', strict=False)


def parser_arc_soft(id, buf, ctx=None):
    ids1 = [m.frame_id for m in db_arc_soft1.messages]
    ids2 = [m.frame_id for m in db_arc_soft2.messages]
    ids = ids1 + ids2
    if id not in ids:
        return None
    elif id in ids1:
        r = db_arc_soft1.decode_message(id, buf, decode_choices=False)
    elif id in ids2:
        r = db_arc_soft2.decode_message(id, buf, decode_choices=False)
    return r


# def parser_pb_can(id, buf, ctx=None):
#     ids = [m.frame_id for m in db_pb_can.messages]
#     if id not in ids:
#         return None
#
#     r = db_pb_can.decode_message(id, buf, decode_choices=False)
#     return r
#
# def parser_ce_can(id, buf, ctx=None):
#     ids = [m.frame_id for m in db_ce_can.messages]
#     if id not in ids:
#         return None
#
#     r = db_ce_can.decode_message(id, buf, decode_choices=False)
#     return r

def parser_rt_can(id, buf, ctx=None):
    ids1 = [m.frame_id for m in db_RT_can1.messages]
    ids2 = [m.frame_id for m in db_RT_can2.messages]
    ids3 = [m.frame_id for m in db_RT_can3.messages]
    ids4 = [m.frame_id for m in db_RT_can4.messages]
    ids5 = [m.frame_id for m in db_RT_can5.messages]
    ids = ids1 + ids2 + ids3+ ids4+ ids5
    if id not in ids:
        return None
    elif id in ids1:
        r = db_RT_can1.decode_message(id, buf, decode_choices=False)
    elif id in ids2:
        r = db_RT_can2.decode_message(id, buf, decode_choices=False)
    elif id in ids3:
        r = db_RT_can3.decode_message(id, buf, decode_choices=False)
    elif id in ids4:
        r = db_RT_can4.decode_message(id, buf, decode_choices=False)
    else:
        r = db_RT_can5.decode_message(id, buf, decode_choices=False)
    return r