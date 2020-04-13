#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/07/15
# @Author  : simon.xu
# @File    : net/ntrip_client.py
# @Desc    :

import nanomsg
from nanomsg import Socket, PAIR, PUB, SUB
import time
import serial
from multiprocessing.dummy import Queue, Process
from threading import Thread
import socket
import datetime
import operator
from functools import reduce


def nmea_checksum(nmea_str):
    return reduce(operator.xor, map(ord, nmea_str), 0)


def run_client(addr='tcp://192.168.98.231:5010'):
    with Socket(SUB) as ssub:
        ssub.connect(addr)
        while True:
            data = ssub.recv()
            print(data)


def run_client_ll(addr):
    q = Queue()
    ntrip = NTRIPClient(addr, q)
    ntrip.start()
    while True:
        try:
            print('attempting serial comm: ttyACM0...')
            ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.5)
        except Exception as e:
            time.sleep(3)
            continue
        print('connected ttyACM0.')
        break
    while True:
        if q.empty():
            time.sleep(0.001)
            continue
        msg = q.get()
        # msg = memoryview(data).tobytes()
        print(len(msg), 'bytes received.')
        ser.write(msg)


class NTRIPClient(Process):
    def __init__(self, addr, queue):
        Process.__init__(self)
        self.queue = queue
        self.addr = addr

    def run(self):
        socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(socket, self.addr)
        while True:
            data = nanomsg.wrapper.nn_recv(socket, 0)[1]
            msg = memoryview(data).tobytes()
            self.queue.put(msg)
            print(len(msg), 'bytes received.')


def generate_gga(lat=22.32112, lon=113.565668):
    t_st = datetime.datetime.utcnow().strftime("%H%M%S.00,")
    ll_st = "{},N,{},E,".format(lat * 100, lon * 100)
    gga_str = "$GPGGA," + t_st + ll_st + "1,04,4.4,3.428,M,-3.428,M,0.0,0000"
    gga_str += '*%02X' % nmea_checksum(gga_str[1:])
    # gga_str = "GPGGA,133622.69,2232.1120000,N,11356.5668000,E,1,00,1.0,3.428,M,-3.428,M,0.0,"
    # print gga_str
    return gga_str


class GGAReporter(Process):
    def __init__(self, host='su.weaty.cn', port=5001):
        Process.__init__(self)
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        # self.lat = lat
        # self.lon = lon
        self.iq = Queue(maxsize=5)

        # self.sock.connect((self.host, self.port))
        # self.gps = open(dev, 'rb')

    def set_pos(self, lat, lon):
        # self.lat = lat
        # self.lon = lon
        if not self.iq.full():
            self.iq.put((lat, lon))

    def run(self):
        print('GGA reporter inited.')
        reconnect = 1

        lat = 22.122222
        lon = 113.566666
        while True:
            if reconnect:
                print('GGA reporter reconnecting...', reconnect)
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((self.host, self.port))
                    print('\033[94m'+'GGA reporter connected'+'\033[0m')
                    reconnect = 0
                except Exception as e:
                    reconnect += 1
                    sleep_interval = 5
                    if reconnect > 5:
                        sleep_interval = 120
                    time.sleep(sleep_interval)
                    continue
            # ggastr = b''
            if self.iq.empty():
                time.sleep(1)
                continue
            while not self.iq.empty():
                lat, lon = self.iq.get()
            print('\033[94m'+'GGA updated:'+'\033[0m', lat, lon)
            ggastr = generate_gga(lat, lon).encode('utf8')
            try:
                self.sock.sendall(ggastr)
            except Exception as e:
                self.info = "error {}".format(e)
                self.sock.close()
                reconnect = 1
            time.sleep(0.8)


def test_rtk_caster(addr):
    from parsers import rtcm3
    sock = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
    nanomsg.wrapper.nn_setsockopt(sock, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
    nanomsg.wrapper.nn_connect(sock, addr)
    time.sleep(0.5)
    gga = GGAReporter('ntrip.weaty.cn')
    gga.start()
    print('start recving rtcm.')
    last_time = 0

    while True:
        data = nanomsg.wrapper.nn_recv(sock, 0)[1]
        if not data:
            time.sleep(0.01)
            continue
        msg = memoryview(data).tobytes()
        print(len(msg), 'bytes RTCM received.')
        now = time.time()
        if now - last_time > 1.0:
            gga.set_pos(22.123456, 113.123456)
            last_time = now


if __name__ == "__main__":
    # run_client_ll('tcp://42.159.10.237:5010')
    test_rtk_caster('tcp://ntrip.weaty.cn:5010')