import time
from multiprocessing import Process, Event, Queue
import os

from parsers.parser import parsers_dict
from parsers.pim222 import parse_pim222
from utils import logger


class SinkManage(Process):
    """
    信号管理类，对信号进行解析、修改操作
    """
    def __init__(self):
        super().__init__()
        self.decode_queue = Queue(30000)                # 解析队列
        self.result_queue = Queue(30000)                # 消息队列
        self.exit = Event()                             # 退出控制

        self.context = {}                               # 基于source字段提供上下文空间
        self.decode_dict = {                            # 解析方法集合
            "can": self.can_decode,
            "q4_100": self.q4_decode,
            "default": self.default_decode
        }

    def run(self):
        logger.warning("decode process starting, pid: {}".format(os.getpid()))
        while not self.exit.is_set():
            msg = self.decode_queue.get()

            if isinstance(msg, tuple):
                # 直接将原数据放入结果队列
                self.result_queue.put(msg)
            elif msg.get("type") and self.decode_dict.get(msg["type"]):
                # 带有解析类型的进行解析处理
                self.decode_dict.get(msg["type"], "default")(msg)
        logger.warning("decode process exiting, pid:".format(os.getpid()))

    # ****************** 操作类方法 ******************

    def put_decode(self, msg):
        """
        加入解码队列
        :param msg:
        :return:
        """
        self.decode_queue.put(msg)

    def put_result(self, msg):
        """
        将不用解析的数据直接放入结果队列
        :param msg:
        :return:
        """
        self.result_queue.put(msg)

    def pop_resulte(self):
        """
        获取结果
        :return:
        """
        if not self.result_queue.empty():
            # print("pop result", self.result_queue.qsize())
            return self.result_queue.get()

    def close(self):
        """
        退出
        :return:
        """
        self.exit.set()

    # ****************** 解码类方法 ******************

    def can_decode(self, msg):
        """
        can信号数据解析
        :param msg: 原数据
        :return:
        """
        source = msg.get("source")
        data = msg.get("data")
        parsers = msg.get("parsers")
        can_id = msg.get("cid")
        timestamp = msg.get("ts")

        if not self.context.get(source):
            self.context[source] = {"source": source}

        ret = None
        for parser in parsers:
            ret = parser(can_id, data, self.context[source])
            if ret is not None:
                break

        if ret is None:
            return

        if isinstance(ret, list):
            for idx, obs in enumerate(ret):
                ret[idx]['ts'] = timestamp
                ret[idx]['source'] = source
                # if ret[idx].get("sensor") and ret[idx]["sensor"] == "ifv300":
                #     print(ret[idx])
        elif isinstance(ret, dict):
            ret['ts'] = timestamp
            ret['source'] = source
        else:
            return

        # 解析后直接放入消息队列
        self.result_queue.put((can_id, ret.copy(), source))
        # print(ret)

    def pim222_decode(self, msg):
        source = msg.get("source")
        data = msg.get("data")

        if not self.context.get(source):
            self.context[source] = {"source": source}
        r = parse_pim222(None, data, self.context)
        if r:
            r['source'] = source
            self.result_queue.put((0x00, r, r['source']))

    def q4_decode(self, msg):
        source = msg.get("source")
        data = msg.get("data")
        protocol = msg.get("protocol")
        timestamp = msg.get("ts")

        if not self.context.get(source):
            self.context[source] = {"source": source}

        ret = parsers_dict.get(protocol, "default")(0, data, self.context)
        if ret is None:
            return

        if type(ret) != list:
            ret = [ret]

        for obs in ret:
            obs['ts'] = timestamp
            obs['source'] = source
        self.result_queue.put((protocol, ret.copy(), source))

    def default_decode(self):
        pass
