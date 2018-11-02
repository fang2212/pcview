
from can.interfaces.socketcan import SocketcanBus
from can.message import Message

from .liuqi import protocol as liuqi_p


class CanBase(object):
    """CAN报文读取发送
    Arguments:
        object {[type]} -- [description]
    Keyword Arguments:
        can_name {str} -- CAN的名字, 正式连接设备使用时不能为None，否则不能创建CAN实例
        bitrate {int} -- 比特率 (default: {500000})
    """

    def __init__(self, can_name=None, bitrate=500000):
        if can_name:
            self.bus = SocketcanBus(channel=can_name, bitrate=bitrate)

    def send(self, can_id, data, is_remote_frame=False, extended_id=True, timeout=None):
        """发送帧
        Arguments:
            can_id {16进制数字} -- 如 0x01
            data {list or tuple} -- 8个整型数
        Keyword Arguments:
            timeout {int or float} -- 超时时间(s) (default: {None})
        """
        msg = Message(arbitration_id=can_id, data=bytes(data),
                      is_remote_frame=is_remote_frame, extended_id=extended_id)
        self.bus.send(msg)
        print("Sender sent a message.", msg)

    def recv(self, timeout=None):
        """接收帧
        Keyword Arguments:
            timeout {int or float} -- 超时时间(s) (default: {None})
        Returns:
            {list} -- 帧ID 加上数据个数，总共最大9个元素
        """
        frdata_recv = {}
        try:
            #print("Receiver is waiting for a message...")
            recvmsg = self.bus.recv(timeout)
            #print('recvmsg', recvmsg)
            #frdata_recv['can_id'] = recvmsg.arbitration_id
            frdata_recv['can_id'] = (hex(recvmsg.arbitration_id)[2:]).upper()
            frdata_recv['recv_ts'] = int(recvmsg.timestamp*1000)
            frdata_recv['data'] = [] 
            for item in recvmsg.data:
                # print('recv item', item)
                # frdata_recv.append(hex(item)[2:].zfill(2))
                frdata_recv['data'].append(item)
            #print("Receiver got: ", recvmsg)
        except Exception as err:
            return 'error <CANBasic class>@' + str(err)
        return frdata_recv

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
    can0 = CanBase('can0')                
    while True:
        tmp = can0.recv(7200)
        tmp = can0.parse(tmp, liuqi_p)
        if tmp.get('can_id') == '18FE5BE8':
            print('msg', can0.parse(tmp, liuqi_p))
        # tmp = can0.frdata_recv_to_bin(tmp)
        # print(tmp)

if __name__ == '__main__':
    unit_test()
            
