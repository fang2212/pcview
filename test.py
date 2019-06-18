import asyncio
import aiohttp
import msgpack


async def mm():
    session = aiohttp.ClientSession()
    URL = 'ws://' + '192.168.0.233' + ':24011'
    async with session.ws_connect(URL) as ws:
        msg = {
            'source': 'pcview',
            'topic': 'subscribe',
            'data': 'pcview',
        }
        data = msgpack.packb(msg)
        await ws.send_bytes(data)
        async for msg in ws:
            print(msg)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(mm())
