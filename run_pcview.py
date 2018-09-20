#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'muhongyun'
__version__ = '1.0.1.faa786'
__progname__ = 'pcview'

import sys

from etc import config as config_script
print(sys.argv)
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--ip", help="ip address", type=str)
parser.add_argument("--video", help="是否保存视频，默认保存", type=str)
#parser.add_argument("--alert", help="是否保存警报数据，包括警报日志，用于演示平台，默认不保存",type=str)
parser.add_argument("--log", help="是否保存日志,默认保存", type=str)
parser.add_argument("--raw_type", help="设备发出图像数据类型[color or gray]", type=str)
parser.add_argument("--lane_speed_limit", help="车道显示速度限制", type=int)
parser.add_argument("--all_laneline", help="是否显示所有车道", type=str)
parser.add_argument("--lane_begin", help="显示车道起点", type=str)
parser.add_argument("--lane_end", help="显示车道终点", type=str)
parser.add_argument("--func", help="功能版本[debug,test,pro,fpga]", type=str)
parser.add_argument("--result_path", help="保存地址", type=str)
parser.add_argument("--save_path", help="保存目录", type=str)
args = parser.parse_args()
config_script.load('fpga')

if args.func:
    config_script.load(args.func)

from etc.config import config
from client.pcview_client import PCView

if __name__ == "__main__":
    config.pic.raw_type = 'color'
    if args.raw_type and args.raw_type == 'gray':
        config.pic.raw_type = args.raw_type
    if args.ip:
        config.ip = args.ip
    if args.video:
        config.video = args.video
    if args.log:
        config.save.log = args.log
    if args.lane_speed_limit:
        config.show.lane_speed_limit = args.lane_speed_limit
    if args.lane_begin:
        config.show.lane_begin = args.lane_begin
    if args.lane_end:
        config.show.lane_end = args.lane_end
    if args.result_path:
        config.save.result_path = args.result_path
    if args.save_path:
        config.save.path = args.save_path

    # config.show.lane_speed_limit = 0
    # config.pic.raw_type = 'color'
    # config.ip = '192.168.1.233'
    # config.pic.use = False
    print("ip", config.ip)
    #config.can.use = 0
    config.save.path = '/home/minieye/pcview_data/'

    pc_view = PCView()
    pc_view.go()