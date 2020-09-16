#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import sys
import logging
import time
import msgpack
import json
import cv2
import argparse
import numpy as np
from datetime import datetime
from multiprocessing import Process, Queue, Value
from player import BaseDraw

from player import FPSCnt
from sink.nano import NanoGroup, Pkg
from recorder.pcc_hil import CanRecorder, GsensorRecorder, VideoRecorder

pack = os.path.join


def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)


def pcc_rec():
    """app func
    """
    dir = 'pcc_data'
    sink_group = NanoGroup()
    sinks = [
        {
            'ip': '127.0.0.1',
            'port': 1209,
            'msg_type': 'gsensor',
            'add_recv_ts': False,
            'pkg': Pkg.gsensor,
            'queue': Queue(),
        },
        {
            'ip': '127.0.0.1',
            'port': 1208,
            'msg_type': 'can1',
            'add_recv_ts': False,
            'pkg': Pkg.can,
            'queue': Queue()
        },
        {
            'ip': '127.0.0.1',
            'port': 1207,
            'msg_type': 'can0',
            'add_recv_ts': False,
            'pkg': Pkg.can,
            'queue': Queue()
        },
        {
            'ip': '127.0.0.1',
            'port': 1200,
            'msg_type': 'camera',
            'add_recv_ts': False,
            'pkg': Pkg.camera,
            'queue': Queue()
        }
    ]

    recs = {
        'can0': CanRecorder(dir),
        'can1': CanRecorder(dir),
        'gsensor': GsensorRecorder(dir),
        'camera': VideoRecorder(pack(dir, 'video'))
    }
    recs['can0'].set_writer('can0.txt')
    recs['can1'].set_writer('can1.txt')
    recs['gsensor'].set_writer('gsensor.txt')
    recs['camera'].set_writer()

    for sink in sinks:
        sink_group.add_sink(sink)
    sink_group.start()

    while True:
        for sink in sinks:
            queue = sink['queue']
            msg_type = sink['msg_type']
            while not queue.empty():
                data = queue.get()
                recs[msg_type].write(data)
                if msg_type == 'camera':
                    cv2.imshow('hello', data['image'])
                    cv2.waitKey(1)

        time.sleep(0.01)

    
if __name__ == '__main__':
    pcc_rec()