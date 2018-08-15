#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import etc.config
etc.config.config = etc.config.load('m3')
from etc.config import config
from client.pcview_client import PCViewer, Hub
import argparse

if __name__ == "__main__":
    # add on
    # config.show.lane_speed_limit = 0
    # config.ip = '192.168.1.233'
    print("debugviewer Begin")
    print("platform", config.platform)

    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="ip address",
                        type=int)

    args = parser.parse_args()
    if args.video:
        config.save.video = True

    hub = Hub()
    pc_viewer = PCViewer(hub)
    pc_viewer.start()
