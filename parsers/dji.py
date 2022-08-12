import struct
import os
import time
from queue import Queue

CRC8Table = [
    0, 94, 188, 226, 97, 63, 221, 131, 194, 156, 126, 32, 163, 253, 31, 65,
    157, 195, 33, 127, 252, 162, 64, 30, 95, 1, 227, 189, 62, 96, 130, 220,
    35, 125, 159, 193, 66, 28, 254, 160, 225, 191, 93, 3, 128, 222, 60, 98,
    190, 224, 2, 92, 223, 129, 99, 61, 124, 34, 192, 158, 29, 67, 161, 255,
    70, 24, 250, 164, 39, 121, 155, 197, 132, 218, 56, 102, 229, 187, 89, 7,
    219, 133, 103, 57, 186, 228, 6, 88, 25, 71, 165, 251, 120, 38, 196, 154,
    101, 59, 217, 135, 4, 90, 184, 230, 167, 249, 27, 69, 198, 152, 122, 36,
    248, 166, 68, 26, 153, 199, 37, 123, 58, 100, 134, 216, 91, 5, 231, 185,
    140, 210, 48, 110, 237, 179, 81, 15, 78, 16, 242, 172, 47, 113, 147, 205,
    17, 79, 173, 243, 112, 46, 204, 146, 211, 141, 111, 49, 178, 236, 14, 80,
    175, 241, 19, 77, 206, 144, 114, 44, 109, 51, 209, 143, 12, 82, 176, 238,
    50, 108, 142, 208, 83, 13, 239, 177, 240, 174, 76, 18, 145, 207, 45, 115,
    202, 148, 118, 40, 171, 245, 23, 73, 8, 86, 180, 234, 105, 55, 213, 139,
    87, 9, 235, 181, 54, 104, 138, 212, 149, 203, 41, 119, 244, 170, 72, 22,
    233, 183, 85, 11, 136, 214, 52, 106, 43, 117, 151, 201, 74, 20, 246, 168,
    116, 42, 200, 150, 21, 75, 169, 247, 182, 232, 10, 84, 215, 137, 107, 53
]

CRC16Table = [
    0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,
    0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,
    0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,
    0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,
    0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,
    0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,
    0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,
    0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,
    0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,
    0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,
    0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,
    0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,
    0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,
    0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,
    0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,
    0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,
    0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,
    0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,
    0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,
    0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,
    0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,
    0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,
    0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,
    0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,
    0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,
    0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,
    0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,
    0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,
    0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,
    0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,
    0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,
    0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78
]

crc8 = 0
crc8_init = 0x77
crc16_init_rec = 0x5281
crc16_init_com = 0x3692
cnt = 60
crc8_err = 0
crc16_err = 0


def dump_hex(buff):
    remain = len(buff)
    while remain:
        print("%.2x" % ord(buff[-remain]), end='')
        remain = remain - 1


class v1Error(Exception):
    '''V1 msg error class'''

    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.message = msg


class Desc:
    '''class used to describe the layout of a UBlox message'''

    def __init__(self, name, msg_format, fields=[], count_field=None, format2=None, fields2=None):
        self.name = name
        self.msg_format = msg_format
        self.fields = fields
        self.count_field = count_field
        self.format2 = format2
        self.fields2 = fields2


def chkCRC8(bytes):
    # print(bytes)
    crc8 = crc8_init
    ret = 0

    for byte in bytes:
        ret = crc8 ^ byte
        crc8 = CRC8Table[ret]

    return crc8


def chkCRC16(bytes):
    # print(bytes)
    crc16 = crc16_init_com
    ret = 0

    for byte in bytes:
        ret = byte
        crc16 = (crc16 >> 8 & 0xff) ^ CRC16Table[(0xff & crc16) ^ ret]

    return crc16


def getHeader(bytes):
    index = 0
    for idx, byte in enumerate(bytes):
        if byte == '\x55':
            return idx
    return -1


class V1_msg:
    def __init__(self):
        self._buf = b''
        self.state = 'sof'
        self.unpacked = Queue()

    def unpack(self):
        if not self.valid():
            raise v1Error('INVALID MASSAGE')

    def pack(self):
        if not self.valid():
            raise v1Error('INVALID MASSAGE')

    def sender(self):
        return int(self._buf[4])

    def recver(self):
        return int(self._buf[5])

    def seqNum(self):
        (seq,) = struct.unpack("<h", self._buf[6:8])
        return seq

    def cmdType(self):
        return int(self._buf[8])

    def cmdSet(self):
        return int(self._buf[9])

    def cmdID(self):
        return int(self._buf[10])

    def check_crc8(self):
        if chkCRC8(self._buf[0:4]) == 0:
            return True
        else:
            print("crc8 err")
            return False

    @property
    def data(self):
        return self._buf[11:-2]

    def check_crc16(self):
        if chkCRC16(self._buf) == 0:
            return True
        else:
            print("crc16 err")
            return True

    def checksum_valid(self):
        return self.check_crc8() and self.check_crc16()

    def head_synced(self):
        if len(self._buf) == 0:
            return False
        if int(self._buf[0]) != 0x55:
            return False
        if len(self._buf) < 4:
            return True
        if self.check_crc8():
            return True
        else:
            print("crc8 err")
            return False

    def msg_len(self):
        if not self.check_crc8():
            return 0
        (len_ver,) = struct.unpack("<h", self._buf[1:3])
        return len_ver & 0x3ff

    def push(self, data):
        if not isinstance(data, bytes):
            return
        for byte in data:
            self._push(byte.to_bytes(1, 'little'))

    def _push(self, byte):
        # print(self._buf, byte)
        # print(self.state)
        self._buf += byte
        if self.state == 'sof':
            if byte != b'U':  # 0x55
                self._buf = b''
                return
            else:
                self.state = 'verLenL'
        elif self.state == 'verLenL':
            self.state = 'verLenH'
        elif self.state == 'verLenH':
            self.state = 'crc8'
        elif self.state == 'crc8':
            if not self.check_crc8():
                self.state = 'sof'
                # print('crc8 error.', self._buf)
                self._buf = b''
                return
            else:
                self.state = 'sender'
        elif self.state == 'sender':
            self.state = 'receiver'
        elif self.state == 'receiver':
            self.state = 'seqNumL'
        elif self.state == 'seqNumL':
            self.state = 'seqNumH'
        elif self.state == 'seqNumH':
            self.state = 'cmdType'
        elif self.state == 'cmdType':
            self.state = 'cmdSet'
        elif self.state == 'cmdSet':
            self.state = 'cmdID'
        elif self.state == 'cmdID':
            if self.bytes_expected() == 2:
                self.state = 'crc16L'
            else:
                self.state = 'data'
        elif self.state == 'data':
            if self.bytes_expected() - 2 <= 0:
                self.state = 'crc16L'
        elif self.state == 'crc16L':
            self.state = 'crc16H'
        elif self.state == 'crc16H':
            # print(chkCRC16(self._buf[:-2]), self._buf[-2:])
            if self.check_crc16():
                msg = {'cmdID': self.cmdID(), 'cmdSet': self.cmdSet(), 'seq': self.seqNum(), 'cmdType': self.cmdType(), 'sender': self.sender(),
                       'receiver': self.recver(), 'len': self.msg_len(), 'data': self.data, 'raw': self._buf}
                self.unpacked.put(msg)
                self.state = 'sof'
                self._buf = b''
            else:
                self._buf = b''
                # print('crc16 error.', chkCRC16(self._buf[:-2]), self._buf[-2:])
                self.state = 'sof'

    def add(self, bytes):
        self._buf += bytes
        while not self.head_synced() and len(self._buf) > 0:
            self._buf = self._buf[1:]
        if self.bytes_expected() < 0:
            self._buf = b''

    def bytes_expected(self):
        if len(self._buf) < 4:
            return 12 - len(self._buf)
        return self.msg_len() - len(self._buf)

    def valid(self):
        if len(self._buf) > 12 and self.bytes_expected() == 0 and self.checksum_valid():
            return True
        else:
            # print self.bytes_expected()
            if len(self._buf) > 12 and self.bytes_expected() == 0:
                self._buf = b''
            return False


class DJI_dev:
    def __init__(self, devid, index, port, baudrate=115200, timeout=0):
        self.serial_device = port
        self.baudrate = baudrate
        self.dev_id = devid
        self.dev_index = index
        self.receiver = (devid & 0x1f) | ((index & 0x7) << 5)

        if os.path.isfile(self.serial_device):
            self.dev = open(self.serial_device, mode='rb')
        else:
            import serial
            self.dev = serial.Serial(self.serial_device, self.baudrate)

    def close(self):
        self.dev.close()
        self.dev = None

    def write(self, buf):
        return self.dev.write(buf)

    def read(self, n):
        return self.dev.read()

    def send(self, msg):
        if not msg.valid():
            print("msg to be sent not valid")
            self.close()
            return
        self.write(msg._buf)

    def special_handling(self, msg):
        if msg.cmdSet() == 0x00 and msg.cmdID() == 0x0e:
            # if msg._buf[11] != 160:
            #     return
            print(msg._buf[12:-2])

            # if msg.cmdSet() == 0x00 and msg.cmdID() == 0x0c:
            #   rtnCode,

    def receive_msg(self):
        msg = V1_msg()
        while True:
            n = msg.bytes_expected()
            b = self.read(n)
            if not b:
                time.sleep(1)
                continue
                # return
            msg.add(b)
            if msg.valid():
                self.special_handling(msg)
                # msg._buf = ""
                return msg

    def send_msg(self, sender, cmdset, cmdid, payload):
        msg = V1_msg()
        seq = 0
        cmdtype = 0x01 << 5
        length = len(payload) + 13
        length = length | (0x01 << 10)
        msg._buf = struct.pack('<Bh', 0x55, length)
        chk8 = chkCRC8(msg._buf[0:3])
        msg._buf += struct.pack('<BBBhBBB', chk8, sender, self.receiver, seq, cmdtype, cmdset, cmdid)
        msg._buf += payload

        chk16 = chkCRC16(msg._buf)
        msg._buf += struct.pack('<h', chk16)
        # print "length:",len(msg._buf)
        # dump_hex(msg._buf)
        self.send(msg)
