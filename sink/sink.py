import time
from multiprocessing import Process, Event, Queue
import os

from parsers.parser import parsers_dict
from parsers.pim222 import parse_pim222
from utils import logger

context = {}

def can_decode(msg):
    """
    can信号数据解析
    :param msg: 原数据
    :return:
    """
    source = msg.get("source")
    data = msg.get("data")
    parsers = msg.get("parsers")
    dbc = msg.get('dbc')
    can_id = msg.get("cid")
    timestamp = msg.get("ts")

    if not context.get(source):
        context[source] = {"source": source}

    ret = None
    if parsers:
        for parser in parsers:
            ret = parser(can_id, data, context[source])
            if ret is not None:
                break
    else:
        ret = parsers_dict.get(dbc, parsers_dict['default'])(can_id, data, context[source])

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

    return can_id, ret.copy(), source


def pim222_decode(msg):
    source = msg.get("source")
    data = msg.get("data")

    if not context.get(source):
        context[source] = {"source": source}
    r = parse_pim222(None, data, context)
    if r:
        r['source'] = source
        return 0x00, r, r['source']


def q4_decode(msg):
    source = msg.get("source")
    data = msg.get("data")
    protocol = msg.get("protocol")
    timestamp = msg.get("ts")

    if not context.get(source):
        context[source] = {"source": source}

    ret = parsers_dict.get(protocol, "default")(0, data, context)
    if ret is None:
        return

    if type(ret) != list:
        ret = [ret]

    for obs in ret:
        obs['ts'] = timestamp
        obs['source'] = source
    return protocol, ret.copy(), source