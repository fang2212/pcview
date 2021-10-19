import argparse
import asyncio
import logging
import os
import pickle
import time
from multiprocessing import Process, Queue, Event

import aiohttp
import eclient
import sharemem
import websockets
from colorlog import ColoredFormatter

from sink.mmap_queue import MMAPQueue


class WebsocketClient(Process):
    """
    接收线程
    """
    def __init__(self, ip='localhost', port=22000, msg_queue=None):
        super().__init__()
        self.ip = ip
        self.port = port
        self.msg_queue = msg_queue
        self.loop = asyncio.get_event_loop()

    def run(self):
        print("connect cve:", self.ip, self.port, "pid:", os.getpid())
        self.loop.run_until_complete(self.connect())

    # async def connect(self):
    #     async with websockets.connect('ws://{}:{}'.format(self.ip, self.port)) as websocket:
    #         async for msg in websocket:
    #             # print("get data from ws")
    #             self.msg_queue.put(pickle.loads(msg), block=False)

    async def connect(self):
        session = aiohttp.ClientSession()
        URL = 'ws://' + str(self.ip) + ':' + str(self.port)
        async with session.ws_connect(URL) as ws:
            async for msg in ws:
                # print(msg)
                self.msg_queue.put(pickle.loads(msg.data), block=False)



class EClientApi(Process):
    """
    eclient api接口
    """

    def __init__(self, plugin_title_list=None, msg_queue=None):
        super().__init__()
        self.msg_queue = msg_queue
        self.plugin_title_list = plugin_title_list or ['plugin-2DView-1']
        self.plugin_list = []
        self.plugin_request_dict = {}
        self.plugin_request_list = []
        self.exit = Event()

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

    def run(self):
        print("call SDK pid:", os.getpid())
        while not self.exit.is_set():
            msg = self.msg_queue.get(time_out=0.01)
            if msg:
                # print(msg)
                # print(msg)
                self.draw_msg(msg)
        self.eClient.close()
        # self.eClient.loop.run_until_complete(self.connet())

    def send_data(self, msg):
        self.msg_queue.put(msg)
        # self.draw_msg(msg)

    def draw_msg(self, msg):
        msg_type = msg.get('type')
        data = msg.get('data')
        plugin = msg.get("plugin")
        #if msg_type != 'img':
        #    print(msg)
        #return

        if msg_type == 'img':
            #print("img")
            image = self.eClient.createAttachment('shared-memory')
            offset = image.allocForWriting(len(data))
            image.finishWriting()
            self.eClient_men.write_memory(offset, data)
            if self.plugin_request_dict.get(plugin):
                # print('img', plugin, msg)
                self.plugin_request_dict.get(plugin).drawImage(image, 'jpg')
        elif msg_type == 'submit':
            self.eClient.submitPluginRequests(self.plugin_request_list)
        elif msg_type == 'clear':
            if self.plugin_request_dict.get(plugin):
                self.plugin_request_dict[plugin].clearAll()
        else:
            #print("draw")
            if self.plugin_request_dict.get(plugin):
                self.plugin_request_dict[plugin].drawShape(data)

    def close(self):
        self.exit.set()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCP服务端启动程序")
    parser.add_argument('title', nargs='+', help='eclient的插件名称（可多个）')
    parser.add_argument('--ip', default='127.0.0.1', help="CVE ip")
    parser.add_argument('--port', type=int, default=22000, help="CVE设置端口号")
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

    msg_queue = MMAPQueue(1024 * 1024 * 20)
    web_client = WebsocketClient(ip=args.ip, port=args.port, msg_queue=msg_queue)
    api = EClientApi(plugin_title_list=args.title, msg_queue=msg_queue)
    api.start()
    web_client.start()
