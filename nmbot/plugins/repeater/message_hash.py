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
            url: str = seg.data['url']

            if 'multimedia.nt.qq.com.cn' in url:
                url = 'http' + url.removeprefix('https')
                
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    res.update(await response.read())
        else:
            res.update(str(seg).encode('utf8'))
    return res.hexdigest()
            