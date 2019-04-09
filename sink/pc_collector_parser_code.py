'''
将pc-collector采集的数据转化为标准格式
'''
import argparse
import cantools
import json
import shutil
import os
from math import sin, cos, pi, fabs, sqrt
from collections import deque

# 读取dbc文件
db_esr = cantools.database.load_file('dbc_file/ESR+DV3_64Tgt.dbc', strict=False)
db_x1 = cantools.database.load_file('dbc_file/MINIEYE_AEB_20190114.dbc', strict=False)
db_mbq3 = cantools.database.load_file('dbc_file/if300_inst_all.dbc', strict=False)
db_ihc = cantools.database.load_file('dbc_file/dbc/meAHBC3_v1.dbc', strict=False)


def parser_none(id, buf):
    return None


def parser_mbq3(id, data):
    buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in data])
    ids = [m.frame_id for m in db_mbq3.messages]
    if id not in ids:
        return None
    r = db_mbq3.decode_message(id, buf, decode_choices=False)
    r['can_id'] = id
    r['msg_type'] = 'MBQ3'
    return r


def parser_ihc(id, data):
    buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in data])
    ids = [m.frame_id for m in db_ihc.messages]
    if id not in ids:
        return None
    r = db_ihc.decode_message(id, buf, decode_choices=False)
    r['msg_type'] = 'IHC'
    r['can_id'] = id
    return r

def parser_esr(id, data):
    buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in data])
    ids = [m.frame_id for m in db_esr.messages]
    if id not in ids:
        return None
    r = db_esr.decode_message(id, buf, decode_choices=False)
    r['msg_type'] = 'ESR'
    r['can_id'] = id
    return r


def parser_x1(id, data):
    buf = b''.join([int(x, 16).to_bytes(1, 'little') for x in data])
    ids = [m.frame_id for m in db_x1.messages]
    if id not in ids:
        return None
    r = db_x1.decode_message(id, buf, decode_choices=False)
    r['msg_type'] = 'x1'
    r['can_id'] = id
    return r


def parser_gsensor(id, buf):
    r = dict()
    r['msg_type'] = 'Gsensor'
    r['data'] = buf
    return r


def parser_camera(id, buf):
    r = dict()
    r['id'] = int(buf[0])
    r['msg_type'] = 'camera'
    return r


'''
根据CAN信号对应的数据源进行修改
当前信号类型:mbq3 mqb x1 esr
'''
parsers = {
    "CAN0": [parser_mbq3],
    'CAN1': [parser_x1],
    "CAN2": [],
    "CAN3": [parser_esr],
    "CAN4": [parser_ihc],
    "Gsensor": [parser_gsensor],
    "camera": [parser_camera]
}


radar_param = {
    'radar_right_vehicle_edge_dist': 0.76,
    'radar_left_vehicle_edge_dist': 1.04,
    'radar_yaw': -2.4,
    'radar_front_camera_dist': 1.7
}


# 简单的将雷达坐标系转化为摄像头坐标系
def radar2camera(radar, radar_param):
    range = radar['range']
    angle = radar['angle'] - radar_param['radar_yaw']
    radar_diff_y = (radar_param['radar_right_vehicle_edge_dist'] - radar_param['radar_left_vehicle_edge_dist']) / 2
    radar_c = dict()
    radar_c['x'] = range * cos(angle * pi / 180) + radar_param['radar_front_camera_dist']
    radar_c['y'] = range * sin(angle * pi / 180) - radar_diff_y
    return radar_c


# 转化代码
def convert_x1_esr_q3(file_name):
    obs = dict()
    x1_obs = dict()
    x1_ped = dict()
    cipv_idx = 0
    ego_speed = 0
    if not os.path.exists('log'):
        os.makedirs('log')
    wf = open('log/log_q3_x1_can.txt', 'w')

    g_frameid_car = 0
    g_frameid_ped = 0
    cam_frame_id = 0
    pre_video_no = 0

    with open(file_name) as rf:
        for line in rf:
            r = None
            cols = line.strip().split()
            source = cols[2]
            mid = 0
            data = cols[3:]
            if source == 'CAN4':
                continue
            if source == 'CAN0' or source == 'CAN1' or source == 'CAN2' or source == 'CAN3' or source == 'CAN4':
                mid = int(cols[3], 16)
                data = cols[4:]
            for parser in parsers[source]:
                if parser is None:
                    break
                r = parser(mid, data)

                if r and source == 'CAN4':
                    print(cols[0], cols[1], r)

                if r is not None:
                    break
            if r is None:
                continue

            r['ts'] = float(cols[0])*1000 + float(cols[1])/1000
            r['source'] = source
            # output the json file
            # wj.write(json.dumps(r) + '\n')
    # wj.close()
    # return os.path.abspath('log/q3_M_data.json')

            # read x1 data
            if r['msg_type'] == 'x1':
                # get the frame id of the vehicle and the pedestrian
                if r['can_id'] == 1903:
                    g_frameid_car = r['frameid_car']
                if r['can_id'] == 1919:
                    g_frameid_ped = r['frameid_ped']
                # parser the vehicle data
                if 0x770 <= r['can_id'] <= 0x777:
                    index = r['can_id'] - 0x770 + 1
                    obs_num = r['AdditionVehicleNumber' + str(index)]
                    for i in range(obs_num):
                        x1_obs['time'] = r['ts']
                        x1_obs['id'] = r['Target' + str(2 * (index-1) + i + 1) + '_ID']
                        x1_obs['class'] = r['AdditionVehicle' + str(2 * (index-1) + i + 1) + '_Type']
                        x1_obs['x'] = r['AdditionVehicle' + str(2 * (index-1) + i + 1) + '_PosX']
                        x1_obs['y'] = r['AdditionVehicle' + str(2 * (index-1) + i + 1) + '_PosY']
                        x1_obs['ttc'] = 7
                        x1_obs['vx'] = 0
                        x1_obs['cipv'] = 0
                        str_x1 = 'X1_V {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}'.format(g_frameid_car, x1_obs['id'], x1_obs['class'],\
                                  x1_obs['x'], 0, 0, x1_obs['y'], 0, 7, 0)
                        print(line.strip(), file=wf)
                        print(cols[0], cols[1], str_x1, file=wf)
                        x1_obs.clear()
                # parse the key vehicle data 76d+76e
                if r['can_id'] == 0x76d:
                    if r['TargetVehiclePosX'] > 0:
                        x1_obs['time'] = r['ts']
                        x1_obs['id'] = r['TargetID']
                        x1_obs['x'] = r['TargetVehiclePosX']
                        x1_obs['y'] = r['TargetVehiclePosY']
                        x1_obs['fcw'] = r['FCW']
                        x1_obs['cipv'] = 1
                        x1_obs['class'] = r['TargetVehicleType']
                        print(line.strip(), file=wf)
                if r['can_id'] == 0x76e and 'TargetVehicleVelX' in r:
                    if not x1_obs:
                        continue
                    x1_obs['vx'] = r['TargetVehicleVelX']
                    x1_obs['ttc'] = r['TTC']
                    x1_obs['ax'] = r['TargetVehicleAccelX']
                    str_x1 = 'X1_V {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}'.format(g_frameid_car, x1_obs['id'], x1_obs['class'],\
                              x1_obs['x'], x1_obs['vx'], x1_obs['ax'], x1_obs['y'], 0, x1_obs['ttc'], x1_obs['cipv'])
                    print(line.strip(), file=wf)
                    print(cols[0], cols[1], str_x1, file=wf)
                    x1_obs.clear()
                # if r['can_id'] == 0x77a and r['Target_Pedestrian_PosX'] > 0:
                # parse the key pedestrian data
                if r['can_id'] == 0x77a:
                    if r['Target_Pedestrian_PosX'] > 0:
                        x1_ped['time'] = r['ts']
                        x1_ped['id'] = r['Target_Pedestrian_ID']
                        x1_ped['class'] = r['Target_Pedestrian_Type']
                        x1_ped['x'] = r['Target_Pedestrian_PosX']
                        x1_ped['y'] = r['Target_Pedestrian_PosY']
                        x1_ped['cipv'] = 1
                        x1_ped['ttc'] = r['Target_Pedestrian_ttc']
                        str_x1 = 'X1_P {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}'.format(g_frameid_ped, x1_ped['id'], x1_ped['class'],\
                                  x1_ped['x'], 0, 0, x1_ped['y'], 0, x1_ped['ttc'], 1)
                        print(line.strip(), file=wf)
                        print(cols[0], cols[1], str_x1, file=wf)
                        x1_ped.clear()
                if 0x77b <= r['can_id'] <= 0x77d:
                    index = r['can_id'] - 0x77a
                    add_num = r['Addition_Pedestrian_Number' + str(index)]
                    for i in range(add_num):
                        x1_ped['time'] = r['ts']
                        x1_ped['cipv'] = 0
                        x1_ped['ttc'] = 7
                        x1_ped['id'] = r['Addition_Pedestrian_' + str(2 * (index-1) + i + 1) + '_ID']
                        x1_ped['class'] = r['Target_Pedestrian_' + str(2 * (index-1) + i + 1) + '_Type']
                        x1_ped['x'] = r['Addition_Pedestrian_' + str(2 * (index-1) + i + 1) + '_PosX']
                        x1_ped['y'] = r['Addition_Pedestrian_' + str(2 * (index-1) + i + 1) + '_PosY']
                        str_x1 = 'X1_P {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}'.format(g_frameid_ped, x1_ped['id'], x1_ped['class'],\
                                  x1_ped['x'], 0, 0, x1_ped['y'], 0, 7, 0)
                        print(line.strip(), file=wf)
                        print(cols[0], cols[1], str_x1, file=wf)
                        x1_ped.clear()

            # read ESR radar data
            if r['msg_type'] == 'ESR':
                tgt_status = r.get('CAN_TX_TRACK_STATUS')
                if tgt_status is not None:
                    if tgt_status == 1 or tgt_status == 2 or tgt_status == 3 or tgt_status == 4:
                        radar = dict()
                        radar['range'] = r['CAN_TX_TRACK_RANGE']
                        radar['angle'] = r['CAN_TX_TRACK_ANGLE']
                        radar['range_rate'] = r['CAN_TX_TRACK_RANGE_RATE']
                        radar_obs = radar2camera(radar, radar_param)
                        x = radar_obs['x']
                        y = radar_obs['y']
                        # vx = radar['range_rate']
                        # ax = r['CAN_TX_TRACK_RANGE_ACCEL']
                        radar_obs['id'] = r['can_id']
                        radar_obs['vx'] = radar['range_rate'] * cos(radar['angle'] * pi / 180)
                        radar_obs['time'] = r['ts']
                        if fabs(y) < 3:
                            print(line.strip(), file=wf)
                            str_radar = 'radar {0} {1} {2} {3} {4} {5} {6}'.format(r['msg_type'], r['can_id'], \
                                         round(radar_obs['x'], 2), round(radar_obs['y'], 2), round(radar['range_rate'], 2), tgt_status, 0)
                            print(cols[0], cols[1], str_radar, file=wf)

            # read mobileye q3 data
            if r['source'] == 'CAN0' and r['msg_type'] == 'MBQ3':
                lane_tp = 'Q3LANE {0} {1} {2} {3} {4} {5}'
                if 'VIS_LANE_RIGHT_PARALL_A0' in r:
                    str_ = lane_tp.format('right_parall', r['VIS_LANE_RIGHT_PARALL_A0'],
                                            r['VIS_LANE_RIGHT_PARALL_A1'], r['VIS_LANE_RIGHT_PARALL_A2'],
                                            r['VIS_LANE_RIGHT_PARALL_A3'], r['VIS_LANE_RIGHT_PARALL_RANGE'])
                    print(cols[0], cols[1], str_, file=wf)
                if 'VIS_LANE_LEFT_PARALL_A0' in r:
                    str_ = lane_tp.format('left_parall', r['VIS_LANE_LEFT_PARALL_A0'],
                                          r['VIS_LANE_LEFT_PARALL_A1'], r['VIS_LANE_LEFT_PARALL_A2'],
                                          r['VIS_LANE_LEFT_PARALL_A3'], r['VIS_LANE_LEFT_PARALL_RANGE'])
                    print(cols[0], cols[1], str_, file=wf)
                if 'VIS_LANE_RIGHT_INDIVID_A0' in r:
                    str_ = lane_tp.format('right_individ', r['VIS_LANE_RIGHT_INDIVID_A0'],
                                          r['VIS_LANE_RIGHT_INDIVID_A1'], r['VIS_LANE_RIGHT_INDIVID_A2'],
                                          r['VIS_LANE_RIGHT_INDIVID_A3'], r['VIS_LANE_RIGHT_INDIVID_RANGE'])
                    print(cols[0], cols[1], str_, file=wf)
                if 'VIS_LANE_LEFT_INDIVID_A0' in r:
                    str_ = lane_tp.format('left_individ', r['VIS_LANE_LEFT_INDIVID_A0'],
                                          r['VIS_LANE_LEFT_INDIVID_A1'], r['VIS_LANE_LEFT_INDIVID_A2'],
                                          r['VIS_LANE_LEFT_INDIVID_A3'], r['VIS_LANE_LEFT_INDIVID_RANGE'])
                    print(cols[0], cols[1], str_, file=wf)
                if 'VIS_LANE_NEIGHBOR_RIGHT_A0' in r:
                    str_ = lane_tp.format('right_neightbor', r['VIS_LANE_NEIGHBOR_RIGHT_A0'],
                                          r['VIS_LANE_NEIGHBOR_RIGHT_A1'], r['VIS_LANE_NEIGHBOR_RIGHT_A2'], 
                                          r['VIS_LANE_NEIGHBOR_RIGHT_A3'], r['VIS_LANE_NEIGHBOR_RIGHT_RANGE'])
                    print(cols[0], cols[1], str_, file=wf)
                if 'VIS_LANE_NEIGHBOR_LEFT_A0' in r:
                    str_ = lane_tp.format('left_neightbor', r['VIS_LANE_NEIGHBOR_LEFT_A0'],
                                          r['VIS_LANE_NEIGHBOR_LEFT_A1'], r['VIS_LANE_NEIGHBOR_LEFT_A2'],
                                          r['VIS_LANE_NEIGHBOR_LEFT_A3'], r['VIS_LANE_NEIGHBOR_LEFT_RANGE'])
                    print(cols[0], cols[1], str_, file=wf)

                if 'CAN_VEHICLE_SPEED' in r:
                    speed_info = dict()
                    ego_speed = r['CAN_VEHICLE_SPEED']*3.6
                    speed_info['time'] = r['ts']
                    speed_info['speed'] = ego_speed
                    print(cols[0], cols[1], 'speed', str(round(ego_speed, 2)), file=wf)
                if 'VIS_OBS_CIPV' in r:
                    cipv_idx = r['VIS_OBS_CIPV']
                if 'VIS_OBS_COUNT_MSG1' in r:
                    obs['time'] = r['ts']
                    idx = '%02d' % r['VIS_OBS_COUNT_MSG1']
                    if r['VIS_OBS_ID_' + idx] == 0:
                        continue
                    obs['id'] = r['VIS_OBS_ID_' + idx]
                    obs['type'] = 'obstacle'
                    obs['class'] = r['VIS_OBS_CLASSIFICATION_' + idx]
                    obs['height'] = r['VIS_OBS_HEIGHT_' + idx]
                    print(line.strip(), file=wf)
                if 'VIS_OBS_COUNT_MSG2' in r:
                    idx = '%02d' % r['VIS_OBS_COUNT_MSG2']
                    if obs.get('id') is None:
                        continue
                    obs['a_lon'] = r['VIS_OBS_LONG_ACCEL_' + idx]
                    obs['ttc'] = r['VIS_OBS_TTC_CONST_ACC_MODEL_'+idx]
                    obs['CIPO'] = r['VIS_OBS_CIPO_' + idx]
                    print(line.strip(), file=wf)
                if 'VIS_OBS_COUNT_MSG3' in r:
                    idx = '%02d' % r['VIS_OBS_COUNT_MSG3']
                    if obs.get('CIPO') is None:
                        continue
                    obs['width'] = r['VIS_OBS_WIDTH_' + idx]
                    obs['pos_lon'] = r['VIS_OBS_LONG_POS_' + idx]  # + cos(yaw * pi / 180.0) * rg
                    # relative longitudinal velocity
                    obs['vel_lon'] = (r['VIS_OBS_LONG_VEL_' + idx] - ego_speed)/3.6  # + sin(yaw * pi / 180.0) * rg
                    obs['pos_lat'] = r['VIS_OBS_LAT_POS_' + idx]
                    obs['vel_lat'] = r['VIS_OBS_LAT_VEL_' + idx]
                    if cipv_idx == obs['id']:
                        obs['CIPV'] = 1
                    else:
                        obs['CIPV'] = 0
                    str_q3 = 'MBQ3 {0} {1} {2} {3} {4} {5} {6} {7} {8}'.format(obs['id'], obs['class'], round(obs['pos_lon'],2),\
                              round(obs['vel_lon'],2), round(obs['a_lon'],2), round(obs['pos_lat'], 2), round(obs['vel_lat'], 2),\
                              round(obs['ttc'], 2), obs['CIPV'])
                    print(line.strip(), file=wf)
                    print(cols[0], cols[1], str_q3, file=wf)
                    obs.clear()

            # change the format: camera frame-no -> video frame-index
            # unify the data: x1 - esr - q3
            if r['msg_type'] == 'camera':
                dict_video = dict()
                folder_path = os.path.dirname(file_name) + '/video'
                name_lists = os.listdir(folder_path)
                for l in name_lists:
                    if os.path.splitext(l)[1] == '.mp4' or os.path.splitext(l)[1] == '.avi':
                        video_name = os.path.splitext(l)[0]
                        video_name_number = int(video_name[7:])
                        dict_video[video_name_number] = l
                video_no = list(dict_video.keys())
                video_no.sort()
                cam_frame_no = r['id']
                cur_video_no = 0
                cam_frame_raw_id = 0
                if len(video_no) > 1:
                    for i in range(1, len(video_no)):
                        if cam_frame_no < video_no[i]:
                            cur_video_no = video_no[i - 1]
                            cam_frame_raw_id = cam_frame_no - cur_video_no
                            break
                        elif cam_frame_no >= video_no[-1]:
                            cur_video_no = video_no[-1]
                            cam_frame_raw_id = cam_frame_no - cur_video_no
                            break
                    if pre_video_no != cur_video_no:
                        cam_frame_id = 0
                    else:
                        cam_frame_id = cam_frame_id + 1
                    pre_video_no = cur_video_no
                    print(cols[0], cols[1], 'cam_frame', dict_video[cur_video_no], cam_frame_id, file=wf)
                    print(cols[0], cols[1], 'cam_frame_raw_id', dict_video[cur_video_no], cam_frame_raw_id, file=wf)
                else: # one video
                    cur_video_no = video_no[0]
                    cam_frame_raw_id = cam_frame_no - cur_video_no
                    print(cols[0], cols[1], 'cam_frame', dict_video[cur_video_no], cam_frame_id, file=wf)
                    print(cols[0], cols[1], 'cam_frame_raw_id', dict_video[cur_video_no], cam_frame_raw_id, file=wf)
                    cam_frame_id = cam_frame_id + 1

            # read Gsensor data
            if r['msg_type'] == 'Gsensor':
                print(' '.join(cols[i] for i in range(9)), file=wf)

    return os.path.abspath('log/log_q3_x1_can.txt')


def time_sort(file_name, sort_itv=16000):
    """
    sort the log lines according to timestamp.
    :param file_name: path of the log file
    :param sort_itv:
    :return: sorted file path

    """
    # rev_lines = []
    past_lines = deque(maxlen=2 * sort_itv)
    wf = open('log_sort.txt', 'w')
    idx = 0
    with open(file_name) as rf:
        for idx, line in enumerate(rf):
            cols = line.split(' ')
            tv_s = int(cols[0])
            tv_us = int(cols[1])
            ts = tv_s * 1000000 + tv_us
            past_lines.append([ts, line])
            # print(len(past_lines))
            if len(past_lines) < 2 * sort_itv:
                continue
            if (idx + 1) % sort_itv == 0:
                # print(len(past_lines))
                past_lines = sorted(past_lines, key=lambda x: x[0])
                wf.writelines([x[1] for x in past_lines[:sort_itv]])
                past_lines = deque(past_lines, maxlen=2 * sort_itv)
            # if len(past_lines) > 300:  # max lines to search forward.
            #     wf.write(past_lines.popleft()[1])
    past_lines = sorted(past_lines, key=lambda x: x[0])
    wf.writelines([x[1] for x in past_lines[sort_itv - ((idx + 1) % sort_itv):]])

    wf.close()
    return os.path.abspath('log_sort.txt')


if __name__ == "__main__":
    # 处理文件夹下的所有log.txt
    # folder_list = '/media/janker/Extension_Data/work_data/20190307_T5_original_AEBs_test/pc_collect'
    # folder_content_list = os.listdir(folder_list)
    # for f in folder_content_list:
    #     log_name = folder_list + '/' + f + '/log.txt'
    #     if os.path.exists(log_name):
    #         log_sort_name = os.path.join(os.path.dirname(log_name), 'log_sort.txt')
    #         sort_src = time_sort(log_name)
    #         shutil.copy2(sort_src, os.path.dirname(log_name))
    #         os.remove(sort_src)
    #         rdir = os.path.dirname(log_sort_name)
    #         cr = convert_x1_esr_q3(log_sort_name)
    #         shutil.copy2(cr, rdir)

    # 处理一个log.txt

    parser = argparse.ArgumentParser()
    parser.add_argument("--log-path", help="log地址", type=str)
    args = parser.parse_args()
    print('args', args)
    if args.log_path:
        log_name = args.log_path
    
    log_name = 'F:\\EyeQ3\\20190311160558\\log.txt'
    log_name = r'F:\EyeQ3\20190227_ssae_aeb_x1_q3_esr\pc_collect\20190227114920_CCRM_50kmh\log.txt'
    log_name = r'F:\EyeQ3\20190317_ssae_q3\night_data\20190316205142\log.txt'
    log_sort_name = os.path.join(os.path.dirname(log_name), 'log_sort.txt')
    sort_src = time_sort(log_name)
    shutil.copy2(sort_src, os.path.dirname(log_name))
    os.remove(sort_src)
    rdir = os.path.dirname(log_sort_name)
    cr = convert_x1_esr_q3(log_sort_name)
    shutil.copy2(cr, rdir)
