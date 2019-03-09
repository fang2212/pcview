#.!/usr/bin/python
# -*- coding:utf8 -*-
from .bind import TcpSink


class NanoSink(TcpSink):
    '''
    '''
    def __init__(self, ip, port, mess_queue):
        TcpSink.__init__(self, ip, port)
        self.queue = mess_queue

    def run(self):
        while True:
            res = {
                'frame_id': None,
                'img': None,
                'vehicle': {},
                'lane': {},
                'ped': {},
                'tsr': {},
                'extra': {}
            }
            for msg_type in ['camera', 'lane', 'vehicle', 'tsr', 'ped']:
                buf = self.read_msg()
                if len(buf) > 5:
                    if msg_type == 'camera':
                        frame_id, data = self.pkg_camera(buf)
                        res['img'] = data
                    else:
                        frame_id, data = self.pkg_alg(buf)
                        res[msg_type] = data
                    res['frame_id'] = frame_id
            self.queue.put(res)