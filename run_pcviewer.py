#!/usr/bin/env python3
#-*- coding:utf-8 -*-

from etc import config
config.load()
from etc.config import config
from client.pcview_client import PCViewer, Hub
import argparse

if __name__ == "__main__":
    # add on
    # config.show.lane_speed_limit = 0
    # config.ip = '192.168.1.233'
    print("pcview Begin")
    print("platform", config.platform)

    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="video save",
                        type=int)
    parser.add_argument("--ip", help="ip address",
                        type=str)

    args = parser.parse_args()
    if args.video:
        config.save.video = True
    if args.ip:
        config.ip = args.ip

    hub = Hub()
    pc_viewer = PCViewer(hub)
    pc_viewer.start()
