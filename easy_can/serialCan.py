import serial 
import serial.tools.list_ports

class SerialCan():
    MaxDataLen = 32

    def __init__(self, port = None, bitrate=250000, baudrate = 460800, **kws):
        '''
        :param: port: usb串口设备名, 默认选第一个设备
        :param: bitrate: can波特率
        :param: baudrate: 串口波特率
        '''
        if port:
            ports = [port]
        else:
            ports = self.listPort()
            print('valiable port: ', ports)
        #尝试找到可用的usb串口设备
        self.usbSerial = None
        for port in ports:
            try:
                kws.update(dict(port=port, baudrate=baudrate))
                self.usbSerial = serial.Serial(**kws)
                if not self.setBitrate(bitrate):
                    raise Exception("set bitrate failed")
            except Exception as e:
                print(e)
                self.usbSerial = None    
            else:
                break
        if not self.usbSerial:
            raise Exception("not serial-can device found")

    def __del__(self):
        try:
            self.usbSerial.close()
        except Exception:
            pass

    def setBitrate(self, bitrate):
        #设置can波特率
        def sendBitrate(bitrate):
            cmd = self.int2bytes(0x12)
            bitrate = self.int2bytes(bitrate // 5000, 1)
            data = self.int2bytes(0x01) + bitrate
            self.write(cmd, data)
            time.sleep(0.1)

        sendBitrate(bitrate)
        for i in range(10):
            print(i)
            for cmd, data in self.read():
                print(cmd, data)
                if cmd == self.int2bytes(0x92):
                    if data[0] == 00:
                        return True
                    else:
                        return False
            sendBitrate(bitrate)
        return False


    def run(self):
        while True:
            for frameid, data in self.recv():
                print(frameid, data)

    def send(self, frameid, data, fixLen=8):
        '''
        发送数据到can, 
        :param: frameid: 为int型 或 bytes
        :param: data: bytes 或 list
        :param: fixLen: data长度，当data为int类型时可选
        '''
        #print("send: ", frameid, data)
        frameid = self.int2bytes(frameid, fix=4) if isinstance(frameid, int) else frameid
        data = bytes(data) if type(data) in [list, tuple] else data

        flag = self.int2bytes(0x02, fix=1)
        dataLen = self.int2bytes(len(data), fix=1)
        data = flag + frameid + dataLen + data
        cmd = self.int2bytes(0x30, fix=1)
        self.write(cmd, data)

    def recv(self):
        '''
        生成器， 接收can数据
        :return: frameid(hex-str), data(list)
        '''
        for cmd, msg in self.read():
            if cmd == self.int2bytes(0xB1):
                flag = msg[0:1]
                frameid = msg[1:5]
                dataLen = self.bytes2int(msg[5:6])
                if len(msg) == 6 + dataLen:
                    data = msg[6:]
                    data = [n for n in data]    #转成数组
                    frameid = hex(self.bytes2int(frameid))
                    #print("recv: ", frameid, data)
                    yield frameid, data

    def write(self, cmd, data):
        '''
        发送usb串口数据, cmd、data 为bytes
        '''
        startBit = self.int2bytes(0x66cc, fix=2)
        packLen = self.int2bytes(1 + len(data) + 1, fix=2)
        checkStr = packLen + cmd + data
        checkSum = 0
        for i in range(len(checkStr)):
            checkSum += checkStr[i]
        checkSum = checkSum % 256
        checkSum = self.int2bytes(checkSum, fix=1)

        msg = startBit + packLen + cmd + data + checkSum
        self.usbSerial.write(msg)
        #print(hex(self.bytes2int(msg)))

    def read(self):
        '''
        接收usb串口数据
        '''
        try:
            n = self.usbSerial.inWaiting()
            if n:
                buff = self.usbSerial.read(n)
                #print(hex(self.bytes2int(buff)))
                frames = self.parseBuf(buff)
                #print(frames)
                for cmd, data in frames:
                    yield cmd, data
        except:
            print("Oops!  串口读取错误。")        

    @classmethod
    def parseBuf(self, buff):
        '''
        把usb串口buffer解析成数据帧，usbSerial.read会读取缓存区的所有数据，可能会有多帧
        '''
        frames = []
        while True:
            startBit = self.int2bytes(0x66cc)
            ptr = buff.find(startBit)
            if ptr == -1 or len(buff) < ptr+6: # 最小长度 2 + 2 + 1 + 0 + 1 = 6
                break
            packLen = self.bytes2int( buff[ptr+2:ptr+4] )
            if packLen > self.MaxDataLen:   #错误数据，丢弃
                buff = buff[ptr+2:]
            elif len(buff) < ptr + 4 + packLen:
                break
            else:
                cmd = buff[ptr+4:ptr+5]
                data = buff[ptr+5:ptr+4+packLen-1]
                checkSum = buff[ptr+4+packLen-1:ptr+4+packLen]
                frames.append([cmd, data])
                #print(hex(self.bytes2int(buff[ptr:ptr+4+packLen])))
                buff = buff[ptr+4+packLen:]
        return frames

    @classmethod
    def int2bytes(self, num, fix=None):
        '''
        把int类型转成16进制bytes
        '''
        h = hex(num)[2:]
        if len(h)%2 == 1:
            h = '0' + h
        if fix:
            byte = len(h)//2
            if byte < fix:
                h = '00' * (fix-byte) + h
            elif byte > fix:
                h = h[(byte-fix)*2:]
        b = bytes.fromhex(h)
        return b

    @classmethod
    def bytes2int(self, b):
        '''
        把16进制bytes转成int类型
        '''
        h = b.hex()
        num = int(h, 16)
        return num

    @classmethod
    def listPort(self):
        return [port.device for port in serial.tools.list_ports.comports()]

import time
import unittest
from unittest import TestCase
class TestSerialCan(TestCase):
    '''
    需要连接两个usb，
    '''
    

    def test_hex(self):
        num = 0x123
        byte = SerialCan.int2bytes(num)
        self.assertEqual(byte, b'\x01\x23')
        n = SerialCan.bytes2int(byte)
        self.assertEqual(n, num)

    def test_parseBuf(self):
        buff = SerialCan.int2bytes(0x445566cc0010b102000012340800000000000000455666cc0010b1020000)
        res = [b'\xb1', b'\x02\x00\x00\x124\x08\x00\x00\x00\x00\x00\x00\x00E']
        frames = SerialCan.parseBuf(buff)
        self.assertEqual(res, frames[0])

    def test_can(self):
        ports = SerialCan.listPort()
        if len(ports) < 2:
            print("请连接两个usb设备！")
            self.assertRaises(Exception)
        can0 = SerialCan(port=ports[0])
        can1 = SerialCan(port=ports[1])

        sd = list(range(8))
        can1.send(0x123, sd)
        recv = 0
        time.sleep(0.1)
        while not recv:
            for frameid, data in can0.recv():
                recv = 1
                self.assertEqual(frameid, hex(0x123))
                self.assertEqual(data, sd)
        

    def test_packet_loss(self):
        ports = SerialCan.listPort()
        if len(ports) < 2:
            print("请连接两个usb设备！")
            self.assertRaises(Exception)
        can0 = SerialCan(port=ports[0])
        can1 = SerialCan(port=ports[1])

        send_data = [[0x123, [0,0,0,0,0,0,0,i]] for i in range(100) ]
        recv_data = []
        for frameid, data in send_data:
            can0.send(frameid, data)
            time.sleep(0.01)
            for rf, rd in can1.recv():
                rf = int(rf, 16)
                recv_data.append([rf, rd])
        print("###### recv rate: ", len(recv_data)/len(send_data))
        err_num = 0
        for data in send_data:
            if data not in recv_data:
                err_num += 1
        err_rate = err_num / len(send_data)
        print('###### error rate: ', err_rate)


if __name__ == '__main__':
    #can = SerialCan()
    #can.run()
    unittest.main()



