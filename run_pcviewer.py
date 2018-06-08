#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua <pengquanhua@minieye.cc>'
__version__ = '0.1.0'
__progname__ = 'run'

from client.pcview_client import PCViewer
import argparse

def run(ip='192.168.0.233', save_video=1, path='/home/minieye/data/'):
    # PCViewer('/home/minieye/data/', '192.168.1.251', 0, 0, None).start()
    PCViewer(path, ip, int(save_video), 0, None).start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="ip address",
                        type=str)
    parser.add_argument("--video", help="是否保存原始图片，默认不保存",
                        type=str)
    parser.add_argument("--path", help="保存图片的路径",
                        type=str)
    args = parser.parse_args()
    if (args.video) and not args.path:
        print('请设置处理图片保存路径')
    else:
        run(args.ip, args.video, args.path)
