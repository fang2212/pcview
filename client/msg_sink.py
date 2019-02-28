
#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import sys
import logging
import time
import msgpack
import json
from datetime import datetime

import asyncio
import websockets
import numpy as np
import cv2

pack = os.path.join


class SinkError:
    Closed = 32


def convert(data):
    '''
    msgpack dict type value convert
    delete b'
    '''
    if isinstance(data, bytes):  return data.decode('ascii')
    if isinstance(data, dict):   return dict(map(convert, data.items()))
    if isinstance(data, tuple):  return tuple(map(convert, data))
    if isinstance(data, list):   return list(map(convert, data))
    if isinstance(data, set):    return set(map(convert, data))
    return data


class FlowSink(object):

    @classmethod
    async def pcview_flow(cls, uri, msg_queue):
        while True:
            async with websockets.connect(uri) as websocket:
                msg = {
                    'source': 'pcview-client',
                    'topic': 'subscribe',
                    'data': 'pcview',
                }
                data = msgpack.packb(msg)
                await websocket.send(data)

                new_pack = {}
                new_id = -1
                while True:
                    try:
                        data = await websocket.recv()
                        msg = msgpack.unpackb(data, use_list=False)
                        topic = msg[b'topic'].decode('ascii')
                        # print(topic)
                        # print(type(msg[b'data']))
                        try:
                            data = msgpack.unpackb(msg[b'data'], use_list=False)
                        except Exception as err:
                            data = msg[b'data']
                        # send_ts = int(time.time())*1000
                        # print(topic)
                        # print('get data')
                        if b'image_frame_id' in data:
                            image = cv2.imdecode(np.fromstring(data[b'image'], np.uint8), cv2.IMREAD_COLOR)
                            data = {
                                'camera': {
                                    'image': image,
                                    'create_ts': data[b'camera_time']
                                },
                                'frame_id': data[b'image_frame_id'],
                            }
                        elif b'frame_id' in data:
                            data = convert(data)
                        else:
                            frame_id = int.from_bytes(data[4:8], byteorder="little", signed=False)
                            data = data[24:]
                            image = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
                            data = {
                                'camera': {
                                    'image': image,
                                },
                                'frame_id': frame_id
                            }

                        frame_id = data['frame_id']
                        # print(frame_id)
                        if new_id != frame_id:
                            msg_queue.put(new_pack)
                            new_pack = data
                            new_id = data['frame_id']
                        elif new_id == data['frame_id']:
                            for key in data:
                                if key != 'frame_id':
                                    new_pack[key] = data[key]
                        websocket.pong()
                        # time.sleep(0.01)
                    except websockets.exceptions.ConnectionClosed as err:
                        # msg_queue.put(SinkError.Closed)
                        print('Connection was closed:', err)
                        time.sleep(0.1)
                        # flow_bind()
                        break

    @classmethod
    def open_libflow_sink(cls, ip, msg_queue):
        uri = 'ws://'+ip+':24011'
        asyncio.get_event_loop().run_until_complete(
            cls.pcview_flow(uri, msg_queue))