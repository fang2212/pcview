#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file    :   split_recorder_data.py    
@contact :   caofulin@minieye.cc
@date    :   2020/11/17 下午2:35
"""

import os
import time
import cv2
from pcc import PCC
from pcc_replay import LogPlayer, prep_replay
import sys
import traceback

def run(log_path):
    if not os.path.exists(log_path):
        return

    log_dir = os.path.dirname(log_path)
    videos = sorted(os.listdir(os.path.join(log_dir, "video")))
    time_dt = 20

    r_sort, cfg = prep_replay(log_path)

    print("start", log_path, time.time())
    with open(r_sort, "r") as rf:
        cache_ts_file_pos = []
        running = True
        while running:
            pos = rf.tell()
            line = rf.readline()
            if line == "":
                break
            fields = line.split()
            ts, us = fields[:2]
            ts = int(ts) + int(us) / 1e6
            cache_ts_file_pos.append((pos, ts))
            if cache_ts_file_pos[-1][1] - cache_ts_file_pos[0][1] > time_dt:
                cache_ts_file_pos.pop(0)

            if "voice_note" in line:

                pos = rf.tell()
                cache_ts_file_pos.append((pos, ts))

                file_ts = cache_ts_file_pos[0][1]
                data_dir = time.strftime("%Y%m%d-%H%M%S", time.localtime(ts))
                data_dir = data_dir + "_" + fields[-1]
                data_dir = os.path.join(log_dir, data_dir)
                if not os.path.exists(data_dir):
                    os.makedirs(os.path.join(data_dir, "video"))

                os.system("cp {} {}".format(log_dir + "/installation.json", data_dir))
                os.system("cp {} {}".format(log_dir + "/config.json", data_dir))

                file_pos = cache_ts_file_pos[0][0]
                rf.seek(file_pos)
                new_log_wf = open(os.path.join(data_dir, "log.txt"), "w")
                st_camera_id = -1
                ed_camera_id = -1
                while True:
                    line = rf.readline()

                    if line == "":
                        running = False
                        break
                    fields = line.split()
                    ts, us = fields[:2]
                    ts = int(ts) + int(us) / 1e6

                    new_log_wf.write(line)

                    if "camera" == fields[2]:
                        if st_camera_id == -1:
                            st_camera_id = int(fields[3])
                        ed_camera_id = int(fields[3])

                    if ts - file_ts > 2*time_dt:
                        break

                new_log_wf.flush()
                new_log_wf.close()

                rf.seek(cache_ts_file_pos[-1][0])

                while cache_ts_file_pos[-1][1] - cache_ts_file_pos[0][1] > time_dt:
                    cache_ts_file_pos.pop(0)


                print("voice in ", st_camera_id, ed_camera_id)
                odir = data_dir
                replayer = LogPlayer(r_sort, cfg, ratio=0.2, start_frame=st_camera_id, end_frame=ed_camera_id,
                                     loop=None,
                                     nnsend=None, real_interval=None, chmain=None)
                pcc = PCC(replayer, replay=True, rlog=r_sort, ipm=True, save_replay_video=odir, uniconf=cfg)
                replayer.start()
                pcc.start()
                replayer.join()
                pcc.control(ord('q'))
                del replayer
                del pcc

                # for f in videos:
                #     src_video_file = os.path.join(log_dir, "video", f)
                #     cap = cv2.VideoCapture(src_video_file)
                #     total_frame = cap.get(7)
                #     if total_frame == 0: total_frame = 1200
                #     cap.release()
                #     sid = int(f.split("_")[-1][:-4])
                #
                #     print(sid, st_camera_id, ed_camera_id)
                #     if (st_camera_id <= sid + total_frame <= ed_camera_id) or (
                #             sid <= ed_camera_id <= sid + total_frame):
                #
                #         dst_video_file = os.path.join(data_dir, "video")
                #         os.system("cp {} {}".format(src_video_file, dst_video_file))

    print("end", log_path, time.time())


def cp_video(logpath, video_key):

    if not os.path.exists(logpath):
        return

    st_frameid, ed_frameid = -1, -1
    with open(logpath, "r") as rf:
        for line in rf:
            line = line.strip()
            fields = line.split()
            if fields[2] == video_key:
                cam_id = int(fields[-1])
                if st_frameid == -1:
                    st_frameid = cam_id
                ed_frameid = cam_id

    o_dir = os.path.join(os.path.dirname(os.path.dirname(logpath)), video_key)
    n_dir = os.path.join(os.path.dirname(logpath), video_key)

    print(st_frameid, ed_frameid)
    # print(o_dir)
    # print(n_dir)

    if not os.path.exists(n_dir):
        os.makedirs(n_dir)

    avis = sorted([ f for f in os.listdir(o_dir) if f.endswith(".avi")] , key=lambda d: int(d.split("_")[-1][:-4]))
    i, j = 0, 0
    while i < len(avis):
        n_id = int(avis[i].split("_")[-1][:-4])
        if n_id > st_frameid:
            print(n_id)
            break
        i += 1

    i -= 1
    while j < len(avis):
        n_id = int(avis[j].split("_")[-1][:-4])
        if n_id > ed_frameid:
            print(n_id)
            break
        j += 1
    j -= 1

    for k in range(i, j+1):
        os.system("cp %s %s" % (os.path.join(o_dir, avis[k]), n_dir))


def split_log(logpath, video_key):
    log_dir = os.path.dirname(logpath)
    o_dir = os.path.join(log_dir, video_key)

    avis = sorted([f for f in os.listdir(o_dir) if f.endswith(".avi")], key=lambda d: int(d.split("_")[-1][:-4]))
    rf = open(logpath, "r")

    for i, f in enumerate(avis):
        total_frames = 1200
        if i == len(avis) - 1:
            cap = cv2.VideoCapture(os.path.join(o_dir, f))
            total_frames = cap.get(7)
            cap.release()

        wf = open(os.path.join(o_dir, f + ".log"), "w")

        cnt = 0
        while True:
            line = rf.readline().strip()
            if not line:
                break
            print(line, file=wf)
            fields = line.split()
            if fields[2] == video_key:
                cnt += 1

            if cnt >= total_frames:
                break
        wf.flush()
        wf.close()
    rf.close()


if __name__ == '__main__':
    sys.argv.append("/home/cao/data/download/shujuchuli_test/20201220110621/log.txt")

    arg = sys.argv[1]
    if not os.path.exists(arg):
        print(arg, "is not exists\n")
        exit(0)

    if os.path.isdir(arg):
        for f in os.listdir(arg):
            path = os.path.join(arg, f, "log.txt")
            print(path, "start")
            try:
                run(path)
            except Exception as e:
                print(e)
                print(traceback.print_exc())
            print(path, "end")
    else:
        # run(sys.argv[1])
        # cp_video("/home/cao/data/download/shujuchuli_test/20201220110621/20201220-111134_1/log.txt", "x1_algo.3")
        split_log("/home/cao/data/download/shujuchuli_test/20201220110621/log.txt", "x1_algo.3")
