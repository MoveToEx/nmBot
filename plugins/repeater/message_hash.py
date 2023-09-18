from nonebot.adapters import Message
from nonebot.adapters.onebot.v11.event import *

import requests
import hashlib

class MessageHash:
    def hash(msg: Message):
        res = hashlib.md5()
        for seg in msg:
            if seg.type == 'text':
                text = ''.join([ s.strip() for s in seg.data['text'].split() ])
                res.update(text.encode('utf8'))
            elif seg.type == 'image':
                img = requests.get(seg.data['url'])
                res.update(img.content)
            else:
                res.update(str(seg).encode('utf8'))
        return res.hexdigest()
            