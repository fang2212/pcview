import aiohttp
import asyncio
import msgpack


async def test():
    session = aiohttp.ClientSession()
    async with session.ws_connect(url) as ws:
        msg = {
            'source': '2222',
            'topic': 'pcview',
            'data': 'xxxxxxxxxxx',
        }
        data = msgpack.packb(msg)
        await ws.send_bytes(data)
    session.close()


if __name__ == '__main__':
     url = "ws://127.0.0.1:1234"
     loop = asyncio.get_event_loop()
     loop.run_until_complete(test())




