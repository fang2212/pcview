import os
import struct
from multiprocessing import Process, Queue, freeze_support
import nanomsg


class JpegExtractor(object):
    def __init__(self, video_file=None):
        self.video_fp = None
        if video_file is not None:
            self.video_fp = open(video_file, 'rb')
        self.output_path = None
        self.buf = b''
        self.buf_len = int(2 * 1024 * 1024)
        self.done = True

    def open(self, file_name):
        self.video_fp = open(file_name, 'rb')
        self.done = False

    def release(self):
        self.video_fp.close()
        self.video_fp = None
        self.done = True

    def read(self):
        if not self.video_fp:
            return
        a = self.buf.find(b'\xff\xd8')
        b = self.buf.find(b'\xff\xd9')
        while a == -1 or b == -1:
            read = self.video_fp.read(self.buf_len)
            if len(read) == 0:
                self.release()
                return
            self.buf += read
            a = self.buf.find(b'\xff\xd8')
            b = self.buf.find(b'\xff\xd9')

        jpg = self.buf[a:b + 2]
        self.buf = self.buf[b+2:]

        return jpg


class LogSend:
    def __init__(self, log_path):

        self.log_path = log_path
        self.socks = {}
        self.t0 = 0
        self.last_frame = 0
        self.video_files = os.listdir(os.path.dirname(log_path)+'/video')
        self.jpeg_extractor = JpegExtractor()
        self.base_dir = os.path.dirname(self.log_path)

    def init_socket(self):
        self.socks['camera'] = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.PUB)
        nanomsg.wrapper.nn_bind(self.socks['camera'], "tcp://127.0.0.1:1200".encode())
        self.socks['CAN0'] = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.PUB)
        nanomsg.wrapper.nn_bind(self.socks['CAN0'], "tcp://127.0.0.1:1207".encode())
        self.socks['CAN1'] = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.PUB)
        nanomsg.wrapper.nn_bind(self.socks['CAN1'], "tcp://127.0.0.1:1208".encode())
        self.socks['Gsensor'] = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.PUB)
        nanomsg.wrapper.nn_bind(self.socks['Gsensor'], "tcp://127.0.0.1:1209".encode())

    def run(self):
        self.init_socket()
        rf = open(self.log_path)
        line0 = rf.readline().split(' ')
        self.t0 = int(line0[0]) + int(line0[1]) / 1000000

        for line in rf:
            line = line.strip()
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if cols[2] == 'camera':
                frame_id = int(cols[3])
                if self.jpeg_extractor.done:
                    if len(self.video_files) == 0:
                        print("End of video file(s).")
                        break
                    else:
                        video_dir = os.path.join(self.base_dir, 'video')
                        self.jpeg_extractor.open(os.path.join(video_dir, self.video_files[0]))
                jpg = self.jpeg_extractor.read()

                if jpg is None:
                    continue
                msg = b'0' * 4 + frame_id.to_bytes(4, 'little', signed=False) + struct.pack('<d', ts) + jpg
                nanomsg.wrapper.nn_send(self.socks['camera'], msg, 0)

            if cols[2] == 'CAN0' or cols[2] == 'CAN1':
                can_id = int(cols[3], 16).to_bytes(4, 'little')
                data = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                msg = b'0000' + can_id + struct.pack('<d', ts) + data
                nanomsg.wrapper.nn_send(self.socks[cols[2]], msg, 0)

            if cols[2] == 'Gsensor':
                data = [int(x) for x in cols[3:9]]
                msg = struct.pack('<BBhIdhhhhhhhq', 0, 0, 0, 0, ts, data[3], data[4], data[5], data[0], data[1], data[2],
                                  int((float(cols[9]) - 36.53) * 340), 0)
                nanomsg.wrapper.nn_send(self.socks[cols[2]], msg, 0)
            # print('---------', line)
        rf.close()


if __name__ == "__main__":

    freeze_support()
    source = '/home/cao/文档/data_temp/20190319_fusion_q3_new_version/20190319173018/log.txt'
    ls = LogSend(source)
    ls.run()

