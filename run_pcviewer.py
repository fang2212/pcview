#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua <pengquanhua@minieye.cc>'
__version__ = '0.1.0'
__progname__ = 'run'

from client.pcview_client import PCViewer
import argparse

def run(ip='192.168.0.233', save_video=0, save_alert=0, save_log=0, path='/home/minieye/pcviewer-data/', source=None, ispic=1):
    PCViewer(path, ispic, ip, int(save_video), int(save_log), int(save_alert)).start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="ip address",
                        type=str)
    parser.add_argument("--video", help="是否保存视频，默认不保存",
                        type=str)
    parser.add_argument("--alert", help="是否保存警报数据，包括警报日志，用于演示平台，默认不保存",type=str)
    parser.add_argument("--log", help="是否保存日志,默认不保存", type=str)
    parser.add_argument("--path", help="保存路径", type=str)
    parser.add_argument("--ispic", help="the source of image", type=str)
    args = parser.parse_args()
    run(args.ip, args.video, args.alert, args.log, args.path, args.ispic)
