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
                file_ts = cache_ts_file_pos[0][1]
                data_dir = time.strftime("%Y%m%d-%H%M%S", time.localtime(ts))
                data_dir = data_dir + "_" + fields[-1]
                data_dir = os.path.join(log_dir, data_dir)
                # if not os.path.exists(data_dir):
                #     os.makedirs(os.path.join(data_dir, "video"))

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

                    if ts - file_ts >= 2*time_dt:
                        break

                new_log_wf.flush()
                new_log_wf.close()
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

if __name__ == '__main__':
    sys.argv.append("/home/cao/data/download/shujuchuli_test/20201220110621/log.txt")
    run(sys.argv[1])
