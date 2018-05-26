#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua<pengquanhua.minieye.cc>'
__version__ = '0.1.0'
__name____ = 'test'

from client.pcview_client import PCViewer

def run(ip):
    source_path = '/home/tester/minieye/pc-viewer/pc-viewer-data/socket/suit-out'
    save_path = '/home/tester/Documents/pc-viewer-data/rgb'
    PCViewer(save_path, ip, 1, 1).test(source_path)

if __name__ == "__main__":
    ip = "192.168.0.111"
    run(ip)

