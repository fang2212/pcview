#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import etc.config
etc.config.config = etc.config.load('m3')
from etc.config import config
from client.pcview_client import PCView
import argparse

if __name__ == "__main__":
    # add on
    # config.show.lane_speed_limit = 0
    # config.ip = '192.168.1.233'


    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="ip address",
                        type=int)
    parser.add_argument("--cfg", help="ip address",
                        type=str)

    args = parser.parse_args()
    if args.video:
        etc.config.save.video = True
    print("debugviewer Begin")
    print("platform", config.platform)
    # config.msg_types = ['lane', 'vehicle', 'tsr']

    pc_view = PCView()
    pc_view.go()

