#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua<pengquanhua.minieye.cc>'
__version__ = '0.1.0'
__name____ = 'test'

from DemoPlayer import DemoPlayer
import argparse

def run(path):
    DemoPlayer().play(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="data path",
                        type=str)
    args = parser.parse_args()
    path = '/home/minieye/pcviewer-demo-data/201806082023/image/'
    
    #path = '/home/minieye/文档/pc-viewer-data/rgb/201805261134'
    if args.path:
        path = args.path
    run(path)
