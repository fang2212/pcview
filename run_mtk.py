#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua <pengquanhua@minieye.cc>'
__version__ = '0.1.0'
__progname__ = 'run'

from client.pcview_client import PCViewer
from client.pcview_client import MtkHub

if __name__ == "__main__":
    hub = MtkHub()
    pc_viewer = PCViewer(hub)
    pc_viewer.start()
