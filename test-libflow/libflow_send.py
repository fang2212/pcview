import aiohttp
import asyncio
import msgpack
import json
import re


async def test(source_file):

    while True:
        session = aiohttp.ClientSession()
        fp = open(source_file, "r")
        async with session.ws_connect(url) as ws:

            for line in fp:
                line = line.strip()
                print(line)
                msg = {
                    'source': '2222',
                    'topic': 'pcview',
                    'data': msgpack.packb(json.loads(line))
                }
                data = msgpack.packb(msg)
                await ws.send_bytes(data)
        session.close()
        fp.close()


if __name__ == '__main__':
     url = "ws://127.0.0.1:1234"
     loop = asyncio.get_event_loop()
     loop.run_until_complete(test('/home/cao/下载/pcview-funsion/log.txt'))




