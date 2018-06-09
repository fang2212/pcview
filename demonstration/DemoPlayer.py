#!/usr/bin/python
# -*- coding:utf8 -*-

import time
import threading
import json
import os

from multiprocessing import Queue
import cv2
import screeninfo
import socket
class DemoPlayer():
    """演示平台
    """
    def __init__(self):
        self.exit = False
        self.alert_queue = Queue()
    
    def test(self, path):
        """用于测试，读取离线数据"""
        log_file = os.path.join(path, 'demo.json')
        fp = open(log_file, 'r')
        log_contents = fp.readlines()
        fp.close()
        
#        t = threading.Thread(target=self.init_tcp, args=())
#        t.daemon = True
#       t.start()
        
        main_screen = screeninfo.get_monitors()[0]
        sub_screen = None
        if len(screeninfo.get_monitors()) > 1:
            sub_screen = screeninfo.get_monitors()[1]
        cnt = 0
        while not self.exit:
            for data in log_contents:
                alert_data = json.loads(data)
                for img, alert in alert_data.items():
                    pass
                origin_file = os.path.join(path, 'origin', img+'.jpg')
                if not os.path.exists(origin_file):
                    continue
                origin_img = cv2.imread(origin_file)
                result_file = os.path.join(path, 'result', img+'.jpg')
                if not os.path.exists(result_file):
                    continue
                result_img = cv2.imread(result_file)
                
                alert['speed'] = float(alert['speed'])
                alert['ttc'] = float(alert['ttc'])
                self.alert_queue.put(alert)
                if sub_screen:
                    cv2.namedWindow('UI', cv2.WINDOW_NORMAL)
                    cv2.moveWindow('UI', main_screen.width, 0)
                   # cv2.resizeWindow('UI', sub_screen.width, sub_screen.height)
                    cv2.setWindowProperty('UI', cv2.WND_PROP_FULLSCREEN,
                                 cv2.WINDOW_FULLSCREEN)
                    cv2.imshow('UI', result_img)
                
                cv2.namedWindow('ori', cv2.WINDOW_NORMAL)
                cv2.setWindowProperty('ori', cv2.WND_PROP_FULLSCREEN,
                              cv2.WINDOW_FULLSCREEN)
                cv2.moveWindow('ori', 0, 0)
                cv2.imshow('ori', origin_img)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    self.exit = True
                    break
                elif key == 27:
                    cv2.destroyAllWindows()
                    self.exit = True
                    break
    
    def init_tcp(self):
        self.tcp_id = threading.get_ident()
        def tcplink(sock, addr):
            print('Accept new connection from %s:%s...' % addr)
            print(self.alert_queue.qsize())
            while True:
                if self.exit:
                    break
                while self.alert_queue.qsize() > 5:
                    self.alert_queue.get()
                while not self.alert_queue.empty():
                    alert = self.alert_queue.get()
                    print('AAAAAAAAAAAAALLLLLLLLL', alert)
                    if 'lane_warning' in alert:
                        alert['lane_warning'] = alert['lane_warning']
                    sock.send((json.dumps(alert)).encode())
                time.sleep(0.02)
                heart_msg = {
                    'heart': 1
                }
                sock.send((json.dumps(heart_msg)).encode())
            sock.close()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 16888))
        s.listen(5)
        print('Waiting for connection...')
        while True:
            # 接受一个新连接:
            sock, addr = s.accept()
            # 创建新线程来处理TCP连接:
            t = threading.Thread(target=tcplink, args=(sock, addr))
            t.start()
