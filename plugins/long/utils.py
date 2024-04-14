from nonebot.matcher import Matcher
from nonebot import logger
from nonebot.adapters import Message
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot

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

def extract_image(event: GroupMessageEvent | PrivateMessageEvent):
    res = []
    if event.reply:
        for seg in event.reply.message:
            if seg.type == 'image':
                res.append(seg)
    for seg in event.get_message():
        if seg.type == 'image':
            res.append(seg)
    return res

async def find_user(bot: Bot, kw: str) -> list[int]:
    friends = await bot.get_friend_list()
    if kw.isdigit():
        if int(kw) in [ x['user_id'] for x in friends ]:
            return [ int(kw) ]
        
    res = []

    kw = kw.upper()
    
    for i in friends:
        if i['nickname'].upper().find(kw) != -1 or i['remark'].upper().find(kw) != -1:
            res.append(i['user_id'])
    
    return res
    
async def find_group(bot: Bot, kw: str) -> list[int]:
    groups = await bot.get_group_list()
    if kw.isdigit():
        if int(kw) in [ x['group_id'] for x in groups ]:
            return [ int(kw) ]
        
    res = []

    kw = kw.upper()

    for i in groups:
        if i['group_name'].upper().find(kw) != -1:
            res.append(i['group_id'])

    return res