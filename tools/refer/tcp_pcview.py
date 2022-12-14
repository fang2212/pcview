#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'muhongyun'
__version__ = '1.0.1.faa786'
__progname__ = 'pcview'

import sys
import os
import time

from etc import config as config_script
print(sys.argv)
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--func", help="功能版本[debug,test,pro,fpga],默认fpga", type=str)
parser.add_argument("--ip", help="设备ip address，默认192.168.0.233", type=str)
parser.add_argument("--video", help="是否保存视频[0,1]，默认保存", type=str)
#parser.add_argument("--alert", help="是否保存警报数据，包括警报日志，用于演示平台，默认不保存",type=str)
parser.add_argument("--log", help="是否保存日志[0,1],默认保存", type=str)
parser.add_argument("--raw_type", help="设备发出图像数据类型[color or gray],默认color", type=str)
parser.add_argument("--lane_speed_limit", help="车道显示速度限制,默认50", type=str)
parser.add_argument("--all_laneline", help="是否显示所有车道[0,1]，默认不显示", type=str)
parser.add_argument("--lane_begin", help="显示车道起点，默认460", type=str)
parser.add_argument("--lane_end", help="显示车道终点，默认720", type=str)
parser.add_argument("--result_path", help="保存地址", type=str)
parser.add_argument("--save_path", help="保存目录，默认 ~/pcview_data/", type=str)
parser.add_argument("--show_parameters", help="是否显示左上角的数据，默认不显示", type=str)
parser.add_argument("--use_can", help="打开can", type=str)
args = parser.parse_args()
config_script.load('fpga')

if args.func:
    config_script.load(args.func)

from etc.config import config
from client.pcview_tcp import PCView

if __name__ == "__main__":
    if args.raw_type and args.raw_type == 'gray':
        config.pic.raw_type = args.raw_type
    if args.ip:
        config.ip = args.ip
    if args.video:
        config.save.video = int(args.video)
    if args.log:
        config.save.log = int(args.log)
    if args.all_laneline:
        config.lane.all_laneline = int(args.all_laneline)
    if args.lane_speed_limit:
        config.lane.lane_speed_limit = int(args.lane_speed_limit)
    if args.lane_begin:
        config.lane.lane_begin = int(args.lane_begin)
    if args.lane_end:
        config.lane.lane_end = int(args.lane_end)
    if args.result_path:
        config.save.result_path = args.result_path
    config.save.path = os.path.expanduser('~/pcview_data/')
    if args.save_path:
        config.save.path = args.save_path
    if args.show_parameters:
        config.show.parameters = int(args.show_parameters)
    if args.use_can:
        config.can.use = int(args.use_can)

    config.lane.lane_speed_limit = 0
    # config.pic.raw_type = 'color'
    # config.ip = '192.168.1.233'
    # config.pic.use = False
    print(sys.path)
    print("ip", config.ip)
    #config.can.use = 1
    
    pc_view = PCView()
    pc_view.go()
    while True:
        time.sleep(1)
        print('life')