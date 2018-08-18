#!/usr/bin/env python3
#-*- coding:utf-8 -*-

from etc import config
etc.config.config = etc.config.load('fpga_hil')
from etc.config import config
from client.pcview_client import PCView
from absl import flags as gflags

Flags = gflags.FLAGS

gflags.DEFINE_string('case_path', '', 'RT')
gflags.DEFINE_string('image_floder', '', 'RT')
gflags.DEFINE_string('case_detail', '', 'RT')
gflags.DEFINE_integer('drop_period', 4, 'RT')

if __name__ == "__main__":
    Flags(argv) 

    if args.video:
        etc.config.save.video = True
    print("debugviewer Begin")
    print("platform", config.platform)

    pc_view = PCView()
    pc_view.go()

