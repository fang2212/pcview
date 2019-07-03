import asyncio
import aiohttp
import msgpack
import tkinter as tk
import requests
from PIL import Image, ImageTk
import numpy as np


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
        img = Image.fromarray(np.fromstring(data['data']))
        img = ImageTk.PhotoImage(image=img)
        panel.config(image=img)

    bt1 = tk.Button(window, textvariable=bt1_var, command=record)
    bt1.pack(fill='x')

    bt2 = tk.Button(window, text="refresh", command=refresh)
    bt2.pack(fill='x')

    window.mainloop()


if __name__ == '__main__':
    # read_avi('/home/cao/桌面/20190513_ub482/20190513155950/video/camera_00066945.avi')
    # read_jpg('/home/cao/图片/')
    # test_mini_cv()
    # test_post()
    test_tkinter()