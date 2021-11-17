import argparse
import asyncio
import logging
import pickle
import socket
import threading
import time

import eclient
import sharemem
from colorlog import ColoredFormatter


class EClientApi(object):
    """
    eclient api接口
    """

    def __init__(self, ip='127.0.0.1', port='2200', plugin_title_list=None):
        self.ip = ip  # cve ip地址，获取数据
        self.port = port  # cve port
        self.plugin_title_list = plugin_title_list or ['plugin-2DView-1']
        self.plugin_list = []
        self.plugin_request_dict = {}
        self.plugin_request_list = []

        # 初始化eClient
        self.eClient = eclient.ElectronClient()
        self.eClient.connect()
        mem_info = self.eClient.getSharedMemoryInfo()
        self.eClient_men = sharemem.ShareMem(mem_info['name'], mem_info['size'])
        self.eClient_men.open()

        # 初始化插件请求实例
        for t in self.plugin_title_list:
            plugin = self.eClient.getPluginByTitle(t)
            if plugin:
                self.plugin_list.append(plugin)
                self.plugin_request_dict[t] = self.eClient.createPluginRequest([plugin])
                self.plugin_request_dict[t].clearAll()
                self.plugin_request_list.append(self.plugin_request_dict[t])

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.connet()

    def connet(self):
        self.server.connect((self.ip, self.port))
        recv = threading.Thread(target=self.client_run)
        # listen = threading.Thread(target=self.listen_event)
        recv.start()
        # listen.start()

    def recv_buff(self, size=1024):
        recv_data = self.server.recv(size)
        if len(recv_data):
            return recv_data
        else:
            # 如果数据长度为0 说明客户端断开连接，此时跳出循环关闭套接字
            print('服务端{}下线了......'.format(self.ip, self.port))
            return

    def decode_buff(self, buff):
        """
        对数据进行提取
        :param buff:
        :return:
        """
        try:
            data = pickle.loads(buff)
            if data:
                self.draw_msg(data)
        except Exception as e:
            if len(buff) > 100:
                print("出现错误：{}, 无法解析该内容：{}...{}".format(e, buff[:30], buff[-30:]))
            else:
                print("出现错误：{}, 无法解析该内容：{}".format(e, buff))

    def get_data(self, buff=None, buff_len=0):
        """
        从buff里面获取完整的数据
        :param buff:
        :param buff_len:
        :return:
        """
        msg = b''
        if not buff:
            buff = self.recv_buff(1024)
            if not buff:
                return False

        if buff_len == 0:
            buff_len = int.from_bytes(buff[:4], byteorder='big')
            msg += buff[4:]

        # 计算数据的缺失量
        offset = buff_len - len(msg)
        if offset < 0:
            # 数据里面有多个完整数据，进行提取
            self.decode_buff(msg[:buff_len])

            # 对head长度字节进行完整性判断
            if offset < -4:
                return self.get_data(msg[buff_len:], 0)
            else:
                # 当长度不满4个字节的时候，进行获取补全
                buff = self.recv_buff(1024)
                if buff:
                    return self.get_data(msg[buff_len:]+buff, 0)
                else:
                    return False
        else:
            # 对缺失的数据进行补全
            while len(msg) < buff_len:
                offset = buff_len - len(msg)
                buff_size = 1024 if offset > 1024 else offset
                buff = self.recv_buff(buff_size)
                if buff:
                    msg += buff
                else:
                    return

            self.decode_buff(msg)
            return True

    def client_run(self):
        while True:
            self.get_data()
            # self.listen_event()

    def draw_msg(self, msg):
        msg_type = msg.get('type')
        data = msg.get('data')
        plugin = msg.get("plugin")

        if msg_type == 'img':
            image = self.eClient.createAttachment('shared-memory')
            offset = image.allocForWriting(len(data))
            self.eClient_men.write_memory(offset, data)
            image.finishWriting()
            if self.plugin_request_dict.get(plugin):
                self.plugin_request_dict.get(plugin).drawImage(image, 'jpg')
        elif msg_type == 'submit':
            self.eClient.submitPluginRequests(self.plugin_request_list)
        elif msg_type == 'clear':
            for t in self.plugin_title_list:
                self.plugin_request_dict[t].clearAll()
        else:
            if self.plugin_request_dict.get(plugin):
                self.plugin_request_dict[plugin].drawShape(data)

    def listen_event(self):
        event = self.eClient.recv(timeout=0.1)
        if event is None:
            return

        print('listen', event)
        if event['event'] == 'keydown':
            self.send_to_server(event['data'])

    def send_to_server(self, data):
        return
        msg = pickle.dumps(data)
        self.server.send(len(msg).to_bytes(4, byteorder='big') + msg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCP服务端启动程序")
    parser.add_argument('title', nargs='+', help='eclient的插件名称（可多个）')
    parser.add_argument('--ip', default='127.0.0.1', help="CVE ip")
    parser.add_argument('--port', type=int, default=2200, help="CVE设置端口号")
    parser.add_argument('--debug', "-d", action='store_true', help='调试模式', default=False)
    args = parser.parse_args()

    logger = logging.getLogger(__name__)

    LOGFORMAT = "%(log_color)s%(asctime)s  %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
    formatter = ColoredFormatter(LOGFORMAT, datefmt='%H:%M:%S')

    fh = logging.StreamHandler()
    # fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s： %(message)s', datefmt='%H:%M:%S')
    fh.setFormatter(formatter)
    # 初始化日志输出等级
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    api = EClientApi(ip=args.ip, port=args.port, plugin_title_list=args.title)
    api.start()
