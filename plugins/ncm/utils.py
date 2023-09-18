from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
import re

class Timestamp:
    def __init__(self, x):
        ms, word = re.search(r'[(\[](\d+),\d+,?\d?[)\]](\w?)', x).groups()
        ms = int(ms)
        second = ms // 1000
        minute = second // 60
        self.ms = ms % 1000
        self.second = second % 60
        self.minute = minute % 60
        self.word = word

    def format(self, bracket: str = '[]'):
        res = "%c%02d:%02d.%03d%c" % (bracket[0], self.minute, self.second, self.ms, bracket[1])
        if self.word:
            res += self.word
        return res

async def send_forward_msg(bot: Bot, event: Event, message: list):
    info = await bot.get_login_info()
    message = [
        {
            "type": "node",
            "data": {
                "name": 'nmBot',
                "uin": info.get('user_id'),
                "content": x
            }
        } for x in message]
    if isinstance(event, PrivateMessageEvent):
        await bot.call_api('send_private_forward_msg', user_id=event.get_user_id(), messages=message)
    else:
        await bot.call_api('send_group_forward_msg', group_id=event.group_id, messages=message)

def yrc_to_elrc(s: str):
    a = re.split(r'(\[\d+,\d+\])', s)
    if not a[0].startswith('['):
        a.remove(a[0])

    res = ''

    for i in a:
        if i.startswith('['):
            res += '\n'
            res += Timestamp(i).format()
        else:
            for j in re.findall(r'\(\d+,\d+,\d+\)\w', i):
                res += Timestamp(j).format('<>')

    return res
