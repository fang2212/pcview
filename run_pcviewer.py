#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys

from etc import config as config_script
print(sys.argv)
config_script.load('fpga')
if len(sys.argv) >= 2:
    opt = sys.argv[1]
    config_script.load(opt)
from etc.config import config
from client.pcview_client import PCView
from absl import flags as gflags

Flags = gflags.FLAGS

gflags.DEFINE_string('case_path', '', 'RT')
gflags.DEFINE_string('image_floder', '', 'RT')
gflags.DEFINE_string('case_detail', '', 'RT')
gflags.DEFINE_integer('drop_period', 4, 'RT')
gflags.DEFINE_string('ip', '', 'RT')
gflags.DEFINE_string('raw_type', 'gray', 'RT')

def parse_flag(argv):
    Flags(argv)
    if Flags.ip:
        config.ip = Flags.ip
    config.pic.raw_type = Flags.raw_type

if __name__ == "__main__":
    parse_flag(sys.argv) 

    # config.pic.raw_type = 'color'
    # config.ip = '192.168.1.233'
    config.show.lane_speed_limit = 0
    # config.pic.use = False
    print("debugviewer Begin")
    print("platform", config.platform)
    print("ip", config.ip)

    pc_view = PCView()
    pc_view.go()

