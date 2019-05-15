import aiohttp
import asyncio
import msgpack


async def test():
    session = aiohttp.ClientSession()
    async with session.ws_connect(url) as ws:
        msg = {
            'source': 'pcview',
            'topic': 'subscribe',
            'data': 'pcview'
        }
        data = msgpack.packb(msg)
        await ws.send_bytes(data)

        # 一直等待消息
        async for msg in ws:
            data = msgpack.unpackb(msg.data)
            print(data)
    session.close()


if __name__ == '__main__':
     url = "ws://127.0.0.1:1234"
     loop = asyncio.get_event_loop()
     loop.run_until_complete(test())




