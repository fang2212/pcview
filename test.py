import asyncio
import aiohttp
import msgpack
import tkinter as tk
import requests
from PIL import Image, ImageTk
import numpy as np
import cv2
import base64


def read_jpg(filepath):
    import os
    avi = b''
    filenames = os.listdir(filepath)
    for filename in filenames:
        print(filename)
        if not filename.endswith('.jpg'):
            continue
        filename = os.path.join(filepath, filename)
        i = 0
        with open(filename, 'rb') as bf:
            buf = bf.read()
            avi += buf
            print(buf)
    open('test.avi', 'wb').write(avi)


def read_avi(filename):
    # wf = open('test.log', 'w')
    with open(filename, 'rb') as bf:
        buf = bf.read()
        a = 0
        while a < len(buf):
            b = buf.find(b'\xff\xd8', a)
            return buf[a:b-3]


def test_mini_cv():
    from sink.hub import Hub
    hub = Hub()


    if hub.fileHandler.recording:
        # self.recording = False
        hub.fileHandler.stop_rec()
    else:
        # self.recording = True
        hub.fileHandler.start_rec()
    print('toggle recording status. {}'.format(hub.fileHandler.recording))


def test_post(action):
    data = requests.post('http://localhost:9999', action)

    return data.json()


def test_tkinter():
    window = tk.Tk()
    window.title('pcc')
    # window.geometry('500x300')

    panel = tk.Label(window)  # initialize image panel
    panel.pack(padx=10, pady=10)
    window.config(cursor='arrow')

    img = Image.open(open('/home/cao/图片/Wallpapers/160158-1541059318e139.jpg', 'rb'))
    img = ImageTk.PhotoImage(image=img)
    # print(img)
    panel.config(image=img)

    is_record = False
    bt1_var = tk.StringVar()
    bt1_var.set("start")

    def record():
        if bt1_var.get() == 'recording....':
            action = {'action': 'stop'}
            bt1_var.set("start....")
        else:
            action = {'action': 'start'}
            bt1_var.set("recording....")
        test_post(action)

    def refresh():
        action = {'action': 'image'}
        data = test_post(action)
        # print('refresh', data)
        img = cv2.imdecode(np.fromstring(base64.b64decode(data['data']), np.uint8), cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(img)
        # print('ref', img)
        img = ImageTk.PhotoImage(image=img)
        panel.imgtk = img
        panel.config(image=img)

    bt1 = tk.Button(window, textvariable=bt1_var, command=record)
    bt1.pack(fill='x')

    bt2 = tk.Button(window, text="refresh", command=refresh)
    bt2.pack(fill='x')

    window.mainloop()


def draw_lane(lane_file):
    from player.pcc_ui import Player
    player = Player()
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    video_writer = cv2.VideoWriter("./lane.avi", fourcc, 20.0, (1280, 720), True)
    ctx = []
    speed = 0
    frameid_lane = 0
    with open(lane_file, 'r') as rf:
        for line in rf:
            if 'speed' in line:
                speed = line.split()[1]
                continue

            if 'id' in line:
                frameid_lane = line.split()[1]
                continue

            img = np.zeros([720, 1280, 3], np.uint8)
            fields = line.strip().split()
            c0, c1, c2, c3, end = float(fields[3]), float(fields[4]), float(fields[5]), float(fields[6]), float(fields[-1])
            ctx.append([c0, c1, c2, c3, end])
            if fields[1] == 'Lane4':
                for line in ctx:
                    if int(line[-1]) == 0:
                        continue
                    player.show_lane(img, line[:-1], r=line[-1])
                cv2.putText(img, "speed:"+str(speed) + 'km/h', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255))
                cv2.putText(img, "frameid_lane:" + str(frameid_lane), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255))
                video_writer.write(img)
                cv2.imshow('lane', img)
                cv2.waitKey(1)
                ctx = []


if __name__ == '__main__':
    # read_avi('/home/cao/桌面/20190513_ub482/20190513155950/video/camera_00066945.avi')
    # read_jpg('/home/cao/图片/')
    # test_mini_cv()
    # test_post()
    # test_tkinter()
    draw_lane('/home/cao/下载/log_q3_x1_can.txt')
