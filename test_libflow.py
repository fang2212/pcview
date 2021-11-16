import argparse
import time

import aiohttp
import asyncio
import msgpack

from utils import logger


async def main(ip, port, topic="*"):
    session = aiohttp.ClientSession()
    URL = 'ws://' + str(ip) + ':' + str(port)
    print("准备连接：", URL)
    msg_count = 0
    start_ts = time.time()
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
                long_time = time.time() - start_ts
                logger.warning("fps: {:.2f} recv count:{}/long time:{:.2f}".format(msg_count/long_time, msg_count, long_time))
    except Exception as e:
        logger.error("连接失败：{}".format(e))

if __name__ == "__main__":
    # 初始化命令行方法
    parser = argparse.ArgumentParser(description="测试libflow的端口数据.")
    parser.add_argument('--ip', help="ip地址", required=True)
    parser.add_argument('--port', help="端口号", required=True)
    parser.add_argument('--topic', default="*")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.ip, args.port, args.topic))
