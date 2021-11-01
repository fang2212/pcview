import argparse

import aiohttp
import asyncio
import msgpack


async def main(ip, port, topic="*"):
    session = aiohttp.ClientSession()
    URL = 'ws://' + str(ip) + ':' + str(port)
    print("准备连接：", URL)
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
            print(msg)

if __name__ == "__main__":
    # 初始化命令行方法
    parser = argparse.ArgumentParser(description="测试libflow的端口数据.")
    parser.add_argument('--ip', help="ip地址", required=True)
    parser.add_argument('--port', help="端口号", required=True)
    parser.add_argument('--topic', default="*")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.ip, args.port, args.topic))
