import logging
import os
import pickle
import sys
import time
import socket
import struct
import re
import argparse
import asyncio
import modbus_tk
import modbus_tk.defines as cst
from multiprocessing import Process, Queue, Event
from threading import Thread
from modbus_tk import modbus_tcp

from sink.mmap_queue import MMAPQueue
from utils import logger


class TCPProcess(Thread):
    """
    TCP请求处理进程
    """
    def __init__(self, queue=None, num=None, recv_queue=None):
        super().__init__()
        self.queue = queue
        self.exit = Event()
        self.count = 0
        self.id = num           # 进程序号
        self.recv_queue = recv_queue
        self.client_dict = {}

    async def _run(self):
        while not self.exit.is_set():
            client_msg = self.queue.get()

            client, ip_port = client_msg
            self.count += 1
            self.client_dict[str(ip_port)] = client
            logger.warning("第{}个进程的第{}个连接".format(self.id, self.count))

            # 开启线程处理客户端请求
            await self.client_work(client, ip_port)
            # client_thread = Thread(target=client_work, args=(client, ip_port, self.result_queue))
            # client_thread.start()

    def run(self):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run())

    def send_data(self, data):
        for c in self.client_dict:
            if self.client_dict[c]:
                try:
                    msg = pickle.dumps(data)
                    self.client_dict[c].send(len(msg).to_bytes(4, byteorder='big')+msg)
                except Exception as e:
                    print(e)
                    self.client_dict[c] = None
                    continue

    async def client_work(self, client, ip_port):
        """
        客户端请求处理线程
        :param client: 客户端对象
        :param ip_port: ip跟端口
        :param queue: 结果队列
        :return:
        """
        while True:
            try:
                recv_data = client.recv(1024)
            except Exception as e:
                logger.warning("客户端{}已断开".format(str(ip_port)))
                break

            if len(recv_data):
                try:
                    self.recv_queue.put((ip_port, recv_data.decode("utf-8")))
                except Exception as e:
                    logger.error("出现错误：{}, 无法解析该内容：{}".format(e, recv_data))
            else:
                # 如果数据长度为0 说明客户端断开连接，此时跳出循环关闭套接字
                print('客户端{}下线了......'.format(str(ip_port)))
                break
        client.close()
        self.client_dict[str(ip_port)] = None

    def close(self):
        self.exit.set()


class Server(Thread):
    """
    TCP服务
    """
    def __init__(self, ip="127.0.0.1", port=2200, process_num=1, max_connect=200, send_queue=None, recv_queue=None):
        super().__init__()
        self.ip = ip
        self.port = port
        self.max_connect = max_connect              # 最大连接数
        self.process_num = process_num              # 进程数
        self.process_list = []                      # 进程列表
        self.client_queue_list = []                 # 客户端连接队列
        self.connect_count = 0
        self.send_queue = send_queue                    # 发送队列
        self.recv_queue = recv_queue                    # 接收队列

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server.setblocking(False)
        # self.server.settimeout(0.001)

    def init_process(self):
        """
        初始化处理进程
        :return:
        """
        for i in range(self.process_num):
            client_queue = Queue()
            self.client_queue_list.append(client_queue)
            self.process_list.append(TCPProcess(client_queue, i, recv_queue=self.send_queue))

        for p in self.process_list:
            p.start()

    def run(self):
        self.server.bind((self.ip, self.port))
        self.server.listen(self.max_connect)
        logger.warning("eclient server主进程启动，pid：{}".format(os.getpid()))
        logger.warning("运行端口：{}".format(self.port))
        logger.warning("进程数量：{}, 最多连接数：{}".format(self.process_num, self.max_connect))
        # 初始化处理进程
        self.init_process()

        while True:
            # 接收新的请求连接
            client, ip_port = self.server.accept()

            # 将请求对象传入进程处理
            self.client_queue_list[self.connect_count % self.process_num].put((client, ip_port))
            self.connect_count += 1
            logger.debug("收到第{}个新的请求连接：{}".format(self.connect_count, str(ip_port)))
            # client.close()

    def send_data(self, data):
        for p in self.process_list:
            p.send_data(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCP服务端启动程序")
    parser.add_argument('-pn', '--process_num', type=int, default=4, help="设置进程数")
    parser.add_argument('-mc', '--max_connect', type=int, default=200, help="设置最大连接数")
    parser.add_argument('--debug', "-d", action='store_true', help='调试模式', default=False)
    args = parser.parse_args()

    # 初始化日志输出等级
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    result_queue = Queue()      # 结果队列
    tcp_server = Server(process_num=args.process_num, max_connect=args.max_connect, recv_queue=result_queue)
    tcp_server.start()
