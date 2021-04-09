import sys
import os
import struct
import json
import cv2
import numpy as np
from decode_algo import *



MUDP_HEADER_SIZE = 32 # 8 bytes timestamps + 24 bytes UDP header
BIG_ENDIAN_VERSION_INFO = int('18A1', 16)
STREAM_DEFINITIONS_FOLDER_NAME = 'stream_definitions'

def cal_type_sz_signed(type_str) -> (int, int, bool):

    if type_str in ['double','float64','float64_t','real64_t']:
        return 2, 8, False
    
    if type_str in ['single','float','float32','float32_t','real32_t']:
        return 1, 4, False

    if type_str in ['uint8','uint8_t','unsigned char','bool','boolean','boolean_t','unsigned8_t']:
        return 0, 1, False

    if type_str in ['int8','sint8','int8_t','sint8_t','signed char','char','signed8_t']:
        return 0, 1, True
    
    if type_str in ['uint16','uint16_t','unsigned short','unsigned16_t','bitfield16_t']:
        return 0, 2, False
               
    if type_str in ['int16','sint16','int16_t','sint16_t','signed short','short','signed16_t']:
        return 0, 2, True

    if type_str in ['uint32','uint32_t','unsigned int','unsigned32_t','bitfield32_t']:
        return 0, 4, False

    if type_str in ['int32','sint32','int32_t','sint32_t','signed int','int','signed32_t']:
        return 0, 4, True

    if type_str in ['uint64','uint64_t','unsigned64_t']:
        return 0, 8, False

    if type_str in ['int64','sint64','int64_t','sint64_t','signed64_t']:
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
                for i in range(0, last_len*repeat):
                    data[i] = data[i] + "." + str(i//last_len)

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
                    repeat_buf[-1][1].extend(["uint8 padd"]*padd)
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
        print("expected bytes:", expected_bytes, "real offset:", offset)
        if not os.path.exists("./str_005_016.json"):
            wf = open("./str_005_016.json", "w")
            print(json.dumps(key_data, indent=2), file=wf)
            wf.close()
    return key_data



def decode_header(head: bytes) -> dict:
    
    res = {
            'versionInfo': int.from_bytes( head[8:10], signed=False, byteorder="little"),
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
    hpp_res = decode_hpp(stream_info, data)
    traffic_sign_res = decode_traffic_sign(stream_info, data)
    obs_res = decode_obs(stream_info, data)
    reflect_sign_res = decode_reflect_sign(stream_info, data)
    road_arrow_res = decode_road_arrow(stream_info, data)
    road_border_res = decode_road_border(stream_info, data)
    road_cross_res = decode_road_cross(stream_info, data)
    road_speedlimit_res = decode_road_speedlimit(stream_info, data)
    road_transition_res = decode_road_transition(stream_info, data)
    stopline_res = decode_stop_line(stream_info, data)

    return lane_res, obs_res


def draw_ipm(img, data):
    for d in data:
        if d['type'] == "lane":
            x = np.arange(0, d["range"], 1)            
            y = d['a0'] + d['a1']*x + d['a2'] * np.power(x, 2) + d['a3'] * np.power(x, 3)
            x = 720 - 720 / 200 * x
            y = 480 / 30 * ( y + 15)
            x = x.astype("int32")
            y = y.astype("int32")
            pts = list(zip(y, x))
            for i in range(len(pts)-1):
                cv2.line(img, pts[i], pts[i+1], (255, 0, 0))
        
        elif d['type'] == "obstacle":
            x, y = d['pos_lon'], d['pos_lat']
            x = int(720 - 720 / 200 * x)
            y = int(480 / 30 * ( y + 15))
            if d['class'] == 4:
                cv2.rectangle(img, (y-2, x-2), (y+2, x+6), (0, 255, 0))
            else:
                cv2.rectangle(img, (y-2, x-2), (y+2, x+2), (0, 255, 0))
        
        elif d['type'] == "hpp":
            x = np.arange(d['startRange'], d["endRange"], 1)            
            y = d['a0'] + d['a1']*x + d['a2'] * np.power(x, 2) + d['a3'] * np.power(x, 3)
            x = 720 - 720 / 200 * x
            y = 480 / 30 * ( y + 15)
            x = x.astype("int32")
            y = y.astype("int32")
            pts = list(zip(y, x))
            for i in range(len(pts)-1):
                cv2.line(img, pts[i], pts[i+1], (0, 0, 255))
        elif d['type'] == "road_border":
            x = np.arange(d['startRange'], d["endRange"], 1)            
            y = d['a0'] + d['a1']*x + d['a2'] * np.power(x, 2) + d['a3'] * np.power(x, 3)
            x = 720 - 720 / 200 * x
            y = 480 / 30 * ( y + 15)
            x = x.astype("int32")
            y = y.astype("int32")
            pts = list(zip(y, x))
            for i in range(len(pts)-1):
                cv2.line(img, pts[i], pts[i+1], (255, 255, 0))

        elif d['type'] == 'stop_line':
            x, y = d['longitudinalDistance'], d['lateralDistance']
            x = int(720 - 720 / 200 * x)
            y = int(480 / 30 * ( y + 15))
            cv2.circle(img, (y, x), 2, (255, 0, 255))

        elif d['type'] == 'road_transition':
            x, y = d['transitionLongPosition'], d['transitionLatPosition']
            x = int(720 - 720 / 200 * x)
            y = int(480 / 30 * ( y + 15))
            cv2.circle(img, (y, x), 2, (0, 255, 255))


def decode(mudp_path: str, stream_definitions: dict):
    with open(mudp_path, "rb") as rbf:
        while True:
            header = rbf.read(MUDP_HEADER_SIZE)
            if len(header) < MUDP_HEADER_SIZE:
                break
            header_info = decode_header(header)
            playload_data = rbf.read(header_info["streamChunkLen"])
            if len(playload_data) < header_info["streamChunkLen"]:
                break
            
            if header_info["streamNumber"] == stream_definitions["streamNumber"] and header_info["streamVersion"] == stream_definitions["streamVersion"] and header_info["streamChunkLen"] == stream_definitions["streamChunkLen"]:
                
                data = playload_data
                stream_info = stream_definitions
                lane_res = decode_lane_marker(stream_info, data)
                hpp_res = decode_hpp(stream_info, data)
                traffic_sign_res = decode_traffic_sign(stream_info, data)
                obs_res = decode_obs(stream_info, data)
                reflect_sign_res = decode_reflect_sign(stream_info, data)
                road_arrow_res = decode_road_arrow(stream_info, data)
                road_border_res = decode_road_border(stream_info, data)
                road_cross_res = decode_road_cross(stream_info, data)
                road_speedlimit_res = decode_road_speedlimit(stream_info, data)
                road_transition_res = decode_road_transition(stream_info, data)
                stopline_res = decode_stop_line(stream_info, data)
                light_spots = decode_light_spots(stream_info, data)
                
                # print(len(road_cross_res), len(road_arrow_res), len(light_spots), len(traffic_sign_res), len(reflect_sign_res))
                # lanes, obs = decode_data(playload_data, stream_definitions)
                img = np.zeros([720, 480, 3], dtype=np.uint8)
                draw_ipm(img, lane_res)
                draw_ipm(img, obs_res)
                draw_ipm(img, hpp_res)
                draw_ipm(img, road_border_res)
                draw_ipm(img, stopline_res)
                draw_ipm(img, road_transition_res)
                # print("obs:", len(obs), ",lanes:", len(lanes))
                cv2.imshow("ifv410", img)
                cv2.waitKey(1)

if __name__ == "__main__":
    sys.argv.append("./sample_data/UDP/GACA12H4WD_20200804_C11_103340_002.mudp")
    str_005_016 = read_vis_definiaton("./sample_data/UDP/strdef_src022_str005_ver016_Vis.txt")
    str_005_016.update({'streamNumber': 5, 'streamVersion': 16, "streamChunkLen": 6192})
    decode(sys.argv[1], str_005_016)

