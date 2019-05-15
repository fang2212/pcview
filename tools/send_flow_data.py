
import os
import json
import socketserver
import time
import numpy as np

import msgpack
import cv2

case_path = './cases'

def packMsg(data):
    return msgpack.packb({
        "source": "fd",
        "topic": "pcview",
        "data": data
    })

class Handler(socketserver.BaseRequestHandler):

    def send(self, buf):
        size = len(buf)
        s = size.to_bytes(4, byteorder="big", signed=False)
        print(type(buf), len(buf))
        buf = s + buf
        self.request.sendall(buf)

    def handle(self):
        while 1:
            for p in os.listdir(case_path):
                path = os.path.join(case_path, p)
                if os.path.isdir(path):
                    video_file = os.path.join(path, 'video.avi')
                    log_file = os.path.join(path, 'log.txt')
                    cap = cv2.VideoCapture(video_file)
                    try:
                        with open(log_file, 'r') as log_fp:
                            for line in log_fp.readlines():
                                data = json.loads(line)
                                for key in data:
                                    if key == 'camera':
                                        if data['camera']['create_ts']:
                                            if not cap.isOpened():
                                                print('not cap.isOpened()')
                                                return
                                            ret, image = cap.read()
                                            if not ret.real:
                                                print('not ret.real')
                                                return
                                            image = cv2.imencode('.jpg', image)[1]
                                            print(image.shape)
                                            image = image.tostring()
                                            msg = {
                                                "image_frame_id": data['frame_id'],
                                                "camera_time": data['camera']['create_ts'],
                                                "image": image
                                            }
                                            msg = msgpack.packb(msg)
                                            buf = packMsg(msg)
                                            self.send(buf)
                                    else:
                                        msg = {
                                            "frame_id": data['frame_id'],
                                            key:data[key]
                                        }
                                        msg = msgpack.packb(msg)
                                        buf = packMsg(msg)
                                        self.send(buf)
                                time.sleep(0.05)
                    except Exception as e:
                        print(e)
                    finally:
                        cap.release()

if __name__ == '__main__':
    server = socketserver.TCPServer( ("127.0.0.1", 12032), Handler)
    server.serve_forever()

