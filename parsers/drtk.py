# from . import dji
import struct


def parse_rtk_info(msg, callback=None):
    data = msg['data']
    r = dict()
    r['err_code'] = data[0]
    r['sol_state'] = data[1]
    r['#gps_main'] = data[2]
    r['#bds_main'] = data[3]
    r['#glo_main'] = data[4]
    r['#gps_aux'] = data[5]
    r['#bds_aux'] = data[6]
    r['#glo_aux'] = data[7]
    r['#gps_ref'] = data[8]
    r['#bds_ref'] = data[9]
    r['#glo_ref'] = data[10]
    r['lat_rov'], r['lon_rov'], r['hgt_rov'] = struct.unpack('<ddf', data[11:31])
    r['lat_ref'], r['lon_ref'], r['hgt_ref'] = struct.unpack('<ddf', data[32:52])

    print(r)
    return r


def unpack_unicore(bytes):
    # logger = logging.getLogger('middle_solution')
    # uniSync,msgID,msgType,portAddr,msgLen,seq = struct.unpack("<IhBBhh",bytes[0:12])
    uniSync, msgID, msgType, portAddr, msgLen, seq, idleTime, timeStt, week, ms, rsv2, timeOffset, rsv3 = struct.unpack(
        "<IhBBhhBBhIIhh", bytes[0:28])
    # print('{:x} {} {}'.format(uniSync, timeStt, rsv2))
    # print("Unicore msgID:%d msgType:%d len:%d seq:%.4x week:%d s:%lf timevalid: %d rsv2:%d rsv3:%d" %
    #       (msgID, msgType, msgLen, seq, week, ms/1000.0/60/60/24, timeStt, rsv2, rsv3))
    if msgID == 42:
        solStt, posType, lat, lon, hgt, undulation = struct.unpack("<IIdddf", bytes[28:64])
        trkSVs, solSVs = struct.unpack("<BB", bytes[92:94])
        seq = "[BestPos],%d,%d,%.8f,%.8f,%f,%d,%d,%d,%d" % (
            solStt, posType, lat, lon, hgt, undulation, trkSVs, solSVs, ms)
        print(seq)
        # logger.info(seq)
    if msgID == 283:
        seq = "[BaseRange],%d,%d" % (week, ms)
        # logger.info(seq)

    if msgID == 1023:
        rtkPosType, kHgt, kLat, kLon = struct.unpack('<Ifdd',bytes[28:52])
        psrPosType, pHgt, pLat, pLon, undulation = struct.unpack('<Ifddf',bytes[52:80])
        rtkTrk, rtkSln, psrTrk, psrSln = bytes[80:84]
        # rtkTrk = bytes[80]
        velN, velE, velD = struct.unpack('<ddd', bytes[84:108])
        oriType, length, heading, pitch = struct.unpack('<Ifff', bytes[108:124])
        oriTrk, oriSln = bytes[124:126]
        gdop, pdop, hdop, htdop, tdop, cutoff, trk_satnum, prn = struct.unpack('<ffffffhh', bytes[128:156])
        speed = (velN**2 + velE**2)**0.5
        # print('state {} lat {:.08f} lon {:.08f} hgt {:.03f} speed:{:.2f}m/s #sat {},{},{},{} ori {} yaw {:.3f} len {:.1f} pitch {:.2f}'.format(
        #     rtkPosType, kLat, kLon, kHgt, speed, rtkTrk, rtkSln, psrTrk, psrSln, oriType, heading, length, pitch))
        return {'type': 'rtk', 'rtkst': rtkPosType, 'orist': oriType, 'lat': kLat, 'lon': kLon, 'hgt': kHgt,
                'speed': speed,'velN': velN, 'velE': velE, 'velD': velD, 'length': length, 'yaw': heading,
                'pitch': pitch, 'sat': [rtkTrk, rtkSln, psrTrk, psrSln, oriTrk, oriSln], 'gdop': gdop, 'pdop': pdop,
                'hdop': hdop, 'htdop': htdop, 'tdop': tdop, 'cutoff': cutoff, 'trkSatn': trk_satnum, 'prn': prn}


def parse_rtk_sol(msg, callback):  # 0x50
    return unpack_unicore(msg['data'])


def parse_rtk_status(msg, callback=None):
    data = msg['data']
    r = dict()
    r['msg_type'] = 'rtk_status_0x19'
    r['test_mode'] = data[0]
    r['rtk_flag'], r['single_flag'], r['ori_flag'] = struct.unpack('<hhh', data[1:7])
    # print(r)


def handle_debug(msg, callback):
    data = msg['data']
    # if msg.cmdSet() == 0x00 and msg.cmdID() == 0x0e:
    # if msg._buf[11] != 160:
    #     return
    print('[debug info]', data[12:-2].decode())


def handle_ping_mc(msg, callback):
    # data = msg['data']
    msgid = msg['cmdSet'] << 8 | msg['cmdID']
    print('0x{:04x} RTK ping Flight control!'.format(msgid))
    # send_buf = struct.pack('<BBB', 0x55, 17, 0x04)
    # send_buf += chkCRC8(send_buf[:3]).to_bytes(1, 'little')
    # send_buf += struct.pack('<BBhBBBI', 0x03, 0xfa, 0x00, 0x01, 0x03, 0xfe, 0x3f174301)
    # crc16 = chkCRC16(send_buf[:-2])
    # send_buf += (crc16 & 0xff).to_bytes(1, 'little')
    # send_buf += (crc16 >> 8).to_bytes(1, 'little')
    # can_send(bus, send_buf)
    # for byte in msg['raw']:
    #     print('0x%02x, ' % byte, end='')
    # print('')
    if msgid == 0x000c:
        data = [0x55, 0x0d, 0x04, 0x33, 0x03, 0xfa, 0xbf, 0x00, 0x40, 0x0f, 0xfe, 0x16, 0x2a]
    elif msgid == 0x03fe:
        data = [0x55, 0x0d, 0x04, 0x33, 0xfa, 0x03, 0x59, 0x12, 0x00, 0x03, 0xfe, 0xd1, 0x5c]
    else:
        data = [0x55, 0x0d, 0x04, 0x33, 0x03, 0xfa, 0xbd, 0x00, 0x40, 0x0f, 0xfe, 0x9e, 0x3c]
    callback(data)


def parse_snr(msg):
    data = msg['data']
    snr = []
    sum = 0
    for byte in data:
        snr.append(byte)
        if byte > 0:
            sum += 1
    # if sum > 0:
    #     print('there are satellites.')


v1_handlers = {
    # 0x000e: handle_debug,
    # 0x0f09: parse_rtk_info,
    0x0350: parse_rtk_sol,
    0x0ffe: handle_ping_mc,
    0x03fe: handle_ping_mc,
    # 0x0f19: parse_rtk_status,
    # 0x0f10: parse_snr,
    # 0x0f11: parse_snr,
    # 0x0f12: parse_snr,
    # 0x0f13: parse_snr,
    # 0x0f14: parse_snr,
    # 0x0f15: parse_snr,
    # 0x0f16: parse_snr,
    # 0x0f17: parse_snr,
    # 0x0f18: parse_snr,
    # 0x0fa0: handle_debug
    0x000c: handle_ping_mc,
    0x0001: handle_ping_mc,
    0x0000: handle_ping_mc,
    0x0058: parse_rtk_sol
}


class RTKadapter:
    def __init__(self, comm_dev):
        self.inited = True
        self.activated = True
        self.baseLat = 0.0
        self.baseLon = 0.0
        self.baseHgt = 0.0
        self.comm_dev = comm_dev

    def reboot(self):
        self.comm_dev.send_msg(0x0a, 0x00, 0x0b, payload="")

    def query_status(self):
        self.comm_dev.send_msg(0x0a, 0x00, 0x0c, payload="")

    def query_version(self):
        self.comm_dev.send_msg(0x0a, 0x00, 0x01, payload="")

    def enter_msd_mode(self):
        self.comm_dev.send_msg(0x0a, 0x03, 0x39, payload="")
        self.comm_dev.close()

    def format_sd(self):
        import struct
        self.comm_dev.send_msg(0x0a, 0x03, 0x3a, payload=struct.pack("<b", 1))

    def close(self):
        self.comm_dev.close()
        self.comm_dev = None


class RTKcore:
    def __init__(self, comm_dev):
        self.inited = False
        self.comm_dev = comm_dev

    def reboot(self):
        self.comm_dev.send_msg(0x0a, 0xde, 0x00, 0x0b, payload="")

    def query_version(self):
        self.comm_dev.send_msg(0x0a, 0xde, 0x00, 0x0b, payload="")
