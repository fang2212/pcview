#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua<pengquanhua.minieye.cc>'
__version__ = '0.1.0'
__name____ = 'test'

from client.pcview_client import PCViewer
import argparse

def run(save_demo, path, source):
    source_path = '/media/minieye/testdisk0/Minieye/pc-viewer-data/socket/out'
    save_path = '/home/minieye/Documents/pc-viewer-data/'
    # PCViewer(save_path, None, 0, 1, source).test(source_path)
    PCViewer(save_path, None, 0, int(save_demo), source).test(source_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", help="是否保存处理后图片，默认不保存",
                        type=str)
    parser.add_argument("--path", help="保存图片的路径",
                        type=str)
    parser.add_argument("--source", help="the source of video", type=str)
    args = parser.parse_args()
    if (args.origin or args.result) and not args.path:
        print('请设置处理图片保存路径')
    else:
        run(args.demo, args.path, args.source)

