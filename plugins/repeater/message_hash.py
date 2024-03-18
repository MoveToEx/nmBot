from nonebot.adapters import Message
from nonebot.adapters.onebot.v11.event import *

import aiohttp
import hashlib

async def hash(msg: Message):
    res = hashlib.md5()
    for seg in msg:
        if seg.type == 'text':
            text = ''.join([ s.strip() for s in seg.data['text'].split() ])
            res.update(text.encode('utf8'))
        elif seg.type == 'image':
            session = aiohttp.ClientSession()
            async with session.get(seg.data['url']) as response:
                res.update(await response.read())
                response.close()
            await session.close()
        else:
            res.update(str(seg).encode('utf8'))
    return res.hexdigest()
            