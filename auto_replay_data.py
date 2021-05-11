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
    odir = os.path.dirname(log_path)
    r_sort, cfg = prep_replay(log_path)
    replayer = LogPlayer(r_sort, cfg, ratio=0.2, loop=None, nnsend=None, real_interval=None, chmain=None)
    pcc = PCC(replayer, replay=True, rlog=r_sort, ipm=True, save_replay_video=odir, uniconf=cfg)
    replayer.start()
    pcc.start()
    replayer.join()
    pcc.control(ord('q'))
    del replayer
    del pcc


if __name__ == '__main__':
    sys.argv.append("/home/cao/data/download/shujuchuli_test/20201220110621/log.txt")

    arg = sys.argv[1]
    if not os.path.exists(arg):
        print(arg, "is not exists\n")
        exit(0)

    if os.path.isdir(arg):
        for f in os.listdir(arg):
            log_txt = os.path.join(arg, f, "log.txt")
            replay_avi = os.path.join(arg, f, "replay-render.avi")
            if not os.path.exists(log_txt) or os.path.exists(replay_avi):
                continue
            print(log_txt, "start")
            try:
                run(log_txt)
            except Exception as e:
                print(e)
                print(traceback.print_exc())
            print(log_txt, "end")
    else:
        run(arg)
