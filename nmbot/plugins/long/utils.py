from nonebot.params import *
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot import logger

from typing import overload, Iterable
from io import BytesIO
from aiohttp import ClientSession, ClientError
from pathlib import Path

async def send_forward_msg(bot: Bot, event: Event, message: Iterable[Message]):
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
    elif isinstance(event, GroupMessageEvent):
        await bot.call_api('send_group_forward_msg', group_id=event.group_id, messages=message)

def extract_image(event: GroupMessageEvent | PrivateMessageEvent) -> list[str]:
    res = []
    if event.reply:
        for seg in event.reply.message:
            if seg.type == 'image':
                url = seg.data['url']
                if url.startswith('https://multimedia.nt.qq.com.cn'):
                    url = 'http' + url.removeprefix('https')
                res.append(url)
    for seg in event.get_message():
        if seg.type == 'image':
            res.append(seg.data['url'])
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


async def download_file_to(url: str, dest: Path, session: ClientSession | None) -> None:
    async with session.get(url) as response:
        if response.status == 200:
            with open(dest, 'wb') as f:
                async for chunk, _ in response.content.iter_chunks():
                    f.write(chunk)
    logger.info('downloaded ' + url)

async def fetch(url: str) -> bytes:
    res = BytesIO()
    
    async with ClientSession(trust_env=True) as session:
        async with session.get(url) as response:
            if response.status == 200:
                async for chunk, _ in response.content.iter_chunks():
                    res.write(chunk)
    logger.info('fetched ' + url)

    res.seek(0)
    return res.read()
    