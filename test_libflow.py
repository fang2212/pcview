import argparse
import time

import aiohttp
import asyncio
import msgpack

from colorlog import ColoredFormatter
import logging

logger = logging.getLogger(__name__)

handler = logging.FileHandler("log.txt")
handler.setLevel(logging.INFO)
LOGFORMAT = "%(log_color)s%(asctime)s  %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
formatter = ColoredFormatter(LOGFORMAT, datefmt='%H:%M:%S')
txt_format = "%(asctime)s  %(levelname)s %(message)s"
handler.setFormatter(logging.Formatter(txt_format))

fh = logging.StreamHandler()
# fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s： %(message)s', datefmt='%H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(handler)


async def main(ip, port, args, topic="*"):
    session = aiohttp.ClientSession()
    URL = 'ws://' + str(ip) + ':' + str(port)
    print("准备连接：", URL)
    msg_count = 0
    start_ts = time.time()
    last_ts = time.time()
    tip_ts = time.time()
    try:
        async with session.ws_connect(URL) as ws:
            print("连接端口成功！")
            msg = {
                'source': 'pcview',
                'topic': 'subscribe',
                'data': topic,
            }
            data = msgpack.packb(msg)
            await ws.send_bytes(data)
            async for msg in ws:
                msg_count += 1
                now = time.time()
                long_time = now - start_ts
                last_ts_diff = now - last_ts
                if args.timeout and last_ts_diff > args.timeout:
                    logger.warning("last ts offset:{}".format(last_ts_diff))
                last_ts = now
                if now - tip_ts > 30:
                    print("fps: {:.2f} recv count:{}/long time:{:.2f}".format(msg_count/long_time, msg_count, long_time))
                    tip_ts = now
                if args.show_fps:
                    logger.warning("fps: {:.2f} recv count:{}/long time:{:.2f}".format(msg_count/long_time, msg_count, long_time))
    except Exception as e:
        logger.error("连接失败：{}".format(e))

if __name__ == "__main__":
    # 初始化命令行方法
    parser = argparse.ArgumentParser(description="测试libflow的端口数据.")
    parser.add_argument('--ip', help="ip地址", required=True)
    parser.add_argument('--port', help="端口号", required=True)
    parser.add_argument('--topic', default="*")
    parser.add_argument('--timeout', type=int, help="设置超时时长，设置后会显示到日志上")
    parser.add_argument('--show_fps', action='store_true', help="是否显示fps接收频率")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.ip, args.port, args, args.topic))
