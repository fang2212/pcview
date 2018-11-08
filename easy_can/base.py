import time

from .serialCan import SerialCan
from .liuqi import protocol as liuqi_p


class CanBase(object):
    """CAN报文读取发送
    Arguments:
        object {[type]} -- [description]
    Keyword Arguments:
        can_name {str} -- CAN的名字, 正式连接设备使用时不能为None，否则不能创建CAN实例
        bitrate {int} -- 比特率 (default: {500000})
    """

    def __init__(self, can_name=None):
        self.can = SerialCan(can_name)


    def send(self, can_id, data):
        self.can.send(can_id, data)

    def recv(self):
        """接收帧
        Keyword Arguments:
            timeout {int or float} -- 超时时间(s) (default: {None})
        Returns:
            {list} -- 帧ID 加上数据个数，总共最大9个元素
        """
        for can_id, data in self.can.recv():
            frdata_recv = {}
            frdata_recv['can_id'] = can_id[2:].upper()
            frdata_recv['recv_ts'] = int(time.time()*1000)
            frdata_recv['data'] = data
            yield frdata_recv

    @staticmethod
    def parse(frdata_recv, protocol=liuqi_p):
        can_id = frdata_recv['can_id']
        can_data = frdata_recv['data']
        #print(can_id)
        targets = protocol.get(can_id)
        if not targets:
            return {}

        frdata_recv['info'] = {} 
        for target in targets['info']:
            # print(target)
            start_byte = target['start_byte']
            start_bit = target['start_bit']
            size = target['size']
            if len(can_data) < size:
                continue
            int_val = (can_data[start_byte - 1]>>(start_bit-1)) & ((1<<size)-1)
            target_val = target['offset'] + int_val * target['factor']
            if target_val >= target['min'] and target_val <= target['max']:
                pass
            else:
                target_val = -1
            frdata_recv['info'][target['name']] = target_val
        return frdata_recv

def unit_test():
    can0 = CanBase('/dev/ttyUSB0')            
    while True:    
        for tmp in can0.recv():
            tmp = can0.parse(tmp, liuqi_p)
            print(tmp)
            if tmp.get('can_id') == '18FE5BE8':
                print('msg', can0.parse(tmp, liuqi_p))

if __name__ == '__main__':
    unit_test()
            
