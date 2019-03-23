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

def calc_frame_cost(path):
    content = []
    with open(path, 'r+') as fp:
        content = fp.readlines()
    max_num = 0
    res = {}
    list = []
    for line in content:
        data = json.loads(line)
        loop_index = data[0]['loop_index']
        if loop_index in res:
            res[loop_index]['begin'] = min(res[loop_index]['begin'], data[0]['time'])
            res[loop_index]['end'] = max(res[loop_index]['end'], data[1]['time'])
            res[loop_index]['num'] += 1
            max_num = max(max_num, res[loop_index]['num'])
        else:
            res[loop_index] = {
                'begin': data[0]['time'],
                'end': data[1]['time'],
                'num': 1
            }
            list.append(loop_index)
    list.sort()
    for item in list:
        if res[item]['num'] == max_num:
            print(res[item]['end']-res[item]['begin'])
    print('num', max_num)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="log地址", type=str)
    args = parser.parse_args()
    if not args.path:
        print('input log path')
    else:
        calc_frame_cost(args.path)
