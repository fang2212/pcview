#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua<pengquanhua.minieye.cc>'
__version__ = '0.1.0'
__name____ = 'test'

from client.pcview_client import PCViewer
import argparse

def run(source_path='/home/minieye/pcview-data-rgb/rec_20180526_161914', save_path='/home/minieye/pcviewer-demo-data/'):
    PCViewer(save_path, None, 0, 0, 1, None).test(source_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_path", help="是否保存警报信息和图片，默认保存",
                        type=str)
    parser.add_argument("--save_path", help="保存图片的路径",
                        type=str)
    args = parser.parse_args()
    run(args.source_path, args.save_path)
