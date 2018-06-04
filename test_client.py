#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua<pengquanhua.minieye.cc>'
__version__ = '0.1.0'
__name____ = 'test'

from client.pcview_client import PCViewer

def run(ip):
    source_path = '/media/minieye/testdisk0/Minieye/pc-viewer-data/socket/out'
    save_path = '/home/minieye/Documents/pc-viewer-data/'
    PCViewer(save_path, ip, 1, 1).test(source_path)

if __name__ == "__main__":
    ip = "192.168.0.111"
    run(ip)

