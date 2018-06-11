#!/usr/bin/python
# -*- coding:utf8 -*-

import time
import threading
import json
import os
import numpy as np

from multiprocessing import Queue
import cv2
import screeninfo
import socket

class CVColor(object):
    Red = (0, 0, 255)
    Green = (0, 255, 0)
    Blue = (255, 255, 0)
    Cyan = (255, 255, 0)
    Magenta = (255, 0, 255)
    Yellow = (0, 255, 255)
    Black = (0, 0, 0)
    White = (255, 255, 255)
    Pink = (255, 0, 255)

class Button(object):
    def __init__(self, tl, br):
        self.tl = tl
        self.br = br
        self.x, self.y = tl
        self.x1, self.y1 = br

    def inside(self, x, y):
        return x>=self.x and y>=self.y and x<=self.x1 and y<=self.y1
   
    def draw_button(self, image_content, title, bg=CVColor.White, front_color=CVColor.Black, fix=(5, 18)):
        fix_x, fix_y = fix
        self.title = title
        image_content[self.y:self.y1, self.x:self.x1] = bg
        cv2.putText(image_content, self.title, (self.x+fix_x, self.y+fix_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, front_color, 1, cv2.LINE_AA)

class DemoPlayer():
    """演示平台
    """
    def __init__(self):
        self.exit = False
        self.alert_queue = Queue()
        self.step = 1
        self.flag = 1

    def mouse_event(self, event, x, y, glags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.play_button.inside(x, y):
                if self.flag:
                    self.step = 0
                    self.flag = 0
                    self.play_button.draw_button(self.screen_content, 'play')
                else:
                    self.step = 1
                    self.flag = 1
                    self.play_button.draw_button(self.screen_content, 'pause')
            elif self.exit_button.inside(x, y):
                cv2.destroyAllWindows()
                self.exit = True

    
    def play(self, path):
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
        
            self.screen_content = np.zeros((780, 1280, 3), np.uint8)
            self.play_button = Button((10, 735), (80, 765))
            self.play_button.draw_button(self.screen_content, 'pause')

            self.exit_button = Button((90, 735), (160, 765))
            self.exit_button.draw_button(self.screen_content, 'exit')
        
        while not self.exit:
            index = 0 
            while not self.exit:
                data = log_contents[index]
                index += self.step
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
                    cv2.namedWindow('UI', cv2.WINDOW_AUTOSIZE)
                    cv2.moveWindow('UI', main_screen.width, 0)
                    cv2.resizeWindow('UI', 1280, 720)
                    cv2.setMouseCallback('UI', self.mouse_event)
                    #cv2.setWindowProperty('UI', cv2.WND_PROP_FULLSCREEN,
                    #             cv2.WINDOW_FULLSCREEN)
                    print('shape:', result_img.shape)
                    roi = self.screen_content[0:720, 0:1280]

                    print('shape2:', roi.shape)
                    cv2.addWeighted(result_img, 1, roi, 0, 0.0, roi)
                    cv2.imshow('UI', self.screen_content)

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
