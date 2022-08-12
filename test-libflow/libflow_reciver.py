import aiohttp
import asyncio
import msgpack



def convert(data):
    '''
    msgpack dict type value convert
    delete b'
    '''
    if isinstance(data, bytes):      return data.decode('ascii')
    if isinstance(data, dict):       return dict(map(convert, data.items()))
    if isinstance(data, tuple):      return tuple(map(convert, data))
    if isinstance(data, list):       return list(map(convert, data))
    if isinstance(data, set):        return set(map(convert, data))
    return data


async def run():
    session = aiohttp.ClientSession()
    async with session.ws_connect(url) as ws:

        msg = {
                'source': 'pcview',
                'topic': 'subscribe',
                'data': 'pcview',
        }
        data = msgpack.packb(msg)
        await ws.send_bytes(data)
        async for msg in ws:
            data = msgpack.unpackb(msg.data)
            data = convert(msgpack.unpackb(data[b'data']))
            # data = convert(data)
            # print(data)
            if msg.type in (aiohttp.WSMsgType.CLOSED,
                                aiohttp.WSMsgType.ERROR):
                break


if __name__ == '__main__':
     url = "ws://127.0.0.1:1234"
     loop = asyncio.get_event_loop()
     loop.run_until_complete(run())




