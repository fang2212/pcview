
import os, sys, time, signal
from multiprocessing import Process
import functools
import unittest
from unittest import TestCase
sys.path.append('.')

from etc import config as config_script
config_script.load('test')
from etc.config import config

from client.pcview_client import PCView

def log(func):
    @functools.wraps(func)
    def wrapper(*args, **kws):
        print("#####", "start: ", func.__name__)
        func(*args, **kws)
        print("#####", "end: ", func.__name__)
    return wrapper


class TestPcview(TestCase):
    '''
    测试pcview数据同步及处理功能
    '''

    @log
    def setUp(self):
        config_script.load('fpga')
        self.pcview = PCView()

    def tearDown(self):
        for key in self.pcview.sink:
            if isinstance(self.pcview.sink[key], Process):
                os.kill(self.pcview.sink[key].ident, signal.SIGKILL)
        if isinstance(self.pcview.camera_sink, Process):
                os.kill(self.pcview.camera_sink.ident, signal.SIGKILL)

    @log
    def test_full(self):
        # 有完整的一帧数据
        ts = 123
        frame_id = 1
        self.pcview.cam_queue.put([ts, frame_id, 'img', 'cam'])
        for key in config.msg_types:
            self.pcview.msg_queue.put([ts, frame_id, {"msg_type":key, "frame_id":frame_id}, key])
        res = self.pcview.pop(loop_time=1)
        self.assertNotEqual(res, None)
        self.assertEqual(res['frame_id'], frame_id)
        self.assertEqual(res['img'], 'img')
        self.assertEqual(res['lane'].get('msg_type'), 'lane')

    @log
    def test_lack(self):
        # 缺 vehicle 数据
        ts = 123
        frame_id = 1
        self.pcview.cam_queue.put([ts, frame_id, 'img', 'cam'])
        for key in ['lane']:
                self.pcview.msg_queue.put([ts, frame_id, {"msg_type":key, "frame_id":frame_id}, key])
        res = self.pcview.pop(loop_time=1)
        self.assertEqual(res, None)
    
    @log
    def test_lack_over(self):
        # 缺 vehicle 数据，但帧范围超限制值
        ts = 123
        config.cache_size = 10
        min_frameid = 1
        max_frameid = min_frameid + config.cache_size
        self.pcview.cam_queue.put([ts, max_frameid, 'img', 'cam'])
        for key in ['lane']:
                self.pcview.msg_queue.put([ts, min_frameid, {"msg_type":key, "frame_id":min_frameid}, key])
        res = self.pcview.pop(loop_time=1)
        self.assertNotEqual(res, None)
        self.assertEqual(res['frame_id'], max_frameid)

    @log
    def test_over_no_img(self):
        # 帧范围超限制值但没有图片
        ts = 123
        config.cache_size = 10
        min_frameid = 1
        max_frameid = min_frameid + config.cache_size
        for key in ['lane']:
                self.pcview.msg_queue.put([ts, min_frameid, {"msg_type":key, "frame_id":min_frameid}, key])
        for key in ['lane']:
                self.pcview.msg_queue.put([ts, max_frameid, {"msg_type":key, "frame_id":max_frameid}, key])
        res = self.pcview.pop(loop_time=1)
        self.assertEqual(res, None)

    @log
    def test_fix_frame(self):
        # 测试补帧
        ts = 123
        frame_id = 1
        self.pcview.cam_queue.put([ts, frame_id, 'img', 'cam'])
        for key in config.msg_types:
            self.pcview.msg_queue.put([ts, frame_id, {"data":'aaa', "frame_id":frame_id}, key])

        config.cache_size = 10
        config['fix']['lane'] = 20
        frame_id = frame_id + config['fix']['lane']
        self.pcview.cam_queue.put([ts, frame_id, 'img', 'cam'])
        for key in ['vehicle']:
            self.pcview.msg_queue.put([ts, frame_id, {"data":'bbb', "frame_id":frame_id}, key])
        for key in ['lane']:
            self.pcview.msg_queue.put([ts, 2, {"data":'ccc', "frame_id":frame_id}, key])

        res = self.pcview.pop(loop_time=1)
        self.assertNotEqual(res, None)

        res = self.pcview.pop(loop_time=1)
        self.assertNotEqual(res, None)
        self.assertEqual(res['vehicle']['data'], 'bbb')
        self.assertEqual(res['lane']['data'], 'aaa')



if __name__ == '__main__':
    unittest.main()
        

