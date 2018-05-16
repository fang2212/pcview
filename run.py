#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua <pengquanhua@minieye.cc>'
__version__ = '0.1.0'
__progname__ = 'run'

from client.pcview_client import PCViewer
import argparse

def run(ip, origin_save, result_save, path):
    # PCViewer(path, ip, origin_save, result_save).start()
    # PCViewer('/home/sji32/文档/pcview-data', ip, 1, 1).start()
    PCViewer('/mnt/hgfs/pcview-data', ip, 0, 0).start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="ip address",
                        type=str)
    parser.add_argument("--origin", help="是否保存原始图片，默认不保存",
                        type=str)
    parser.add_argument("--result", help="是否保存处理后图片，默认不保存",
                        type=str)
    parser.add_argument("--path", help="保存图片的路径",
                        type=str)
    args = parser.parse_args()
    if (args.origin or args.result) and not args.path:
        print('请设置处理图片保存路径')
    else:
        run(args.ip, args.origin, args.result, args.path)
