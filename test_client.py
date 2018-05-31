#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua<pengquanhua.minieye.cc>'
__version__ = '0.1.0'
__name____ = 'test'

from client.pcview_client import PCViewer

def run(ip):
    source_path = '/home/minieye/pc-viewer-data/origin'
    save_path = '/home/minieye/文档/new_data/'
    PCViewer(save_path, ip, 0, 0).test(source_path)

if __name__ == "__main__":
    ip = "192.168.0.111"
    run(ip)
