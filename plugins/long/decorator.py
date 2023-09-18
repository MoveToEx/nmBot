from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.message import MessageSegment, Message
import re
import random

from .utils import find_user, find_group

async def _respond(bot: Bot, event: Event, message: Message | str):
    if isinstance(event, PrivateMessageEvent):
        await bot.send_private_msg(user_id=event.user_id, message=message)
    elif isinstance(event, GroupMessageEvent):
        await bot.send_group_msg(group_id=event.group_id, message=message)

class Decorator:
    def __init__(self):
        self.target = None
        self.index = 'random'
        self.repeat = 1
    
    def parse(s: str):
        res = Decorator()
        a = s.split(' ')
        rest = []
        for seg in a:
            if seg.startswith('>'):
                seg = seg[1:].strip()
                if seg.startswith('g') and seg[1:].isdigit():
                    res.target = ('group', int(seg[1:]))
                elif seg.startswith('u') and seg[1:].isdigit():
                    res.target = ('user', int(seg[1:]))
                else:
                    res.target = ('indeterminate', seg)
            elif seg.startswith(':'):
                seg = seg[1:]
                if seg.isdigit():
                    res.index = int(seg)
                elif 'random'.startswith(seg):
                    res.index = 'random'
                elif 'all'.startswith(seg):
                    res.index = 'all'
                else:
                    raise NotImplementedError(seg)
            elif seg.startswith('*'):
                seg = seg[1:]
                if not seg.isdigit():
                    raise NotImplementedError(seg)
                res.repeat = int(seg)
            else:
                rest.append(seg)
        return res, ' '.join(rest)
    
    async def _send_once(self, bot: Bot, event: Event, a: list):
        images = []
        if self.index == 'random':
            images.append(random.choice(a))
        elif self.index == 'all':
            images = a
        elif isinstance(self.index, range):
            images = a[self.index.start:self.index.stop]

        friends = [x['user_id'] for x in await bot.get_friend_list()]
        groups = [x['group_id'] for x in await bot.get_group_list()]

        if self.target:
            if self.target[0] == 'indeterminate':
                res_friends = await find_user(bot, self.target[1])
                res_groups = await find_group(bot, self.target[1])

                if len(res_friends) + len(res_groups) == 0:
                    await _respond(bot, event, f"No target found")
                    return

                if len(res_friends) + len(res_groups) > 1:
                    await _respond(bot, event, f"[ERROR] Identity {self.target[1]} is ambiguous")
                    return
                
                if len(res_friends):
                    self.target = ('user', res_friends[0])

                if len(res_groups):
                    self.target = ('group', res_groups[0])


            if self.target[0] == 'user':
                if not self.target[1] in friends:
                    await _respond(bot, event, f"[ERROR] Bot has not friended {self.target[1]}")
                else:
                    for i in images:
                        await bot.send_private_msg(user_id=self.target[1], message=[
                            MessageSegment.image(i)
                        ])
            elif self.target[0] == 'group':
                if not self.target[1] in groups:
                    await _respond(bot, event, f"[ERROR] Bot has not joined group {self.target[1]}")
                else:
                    for i in images:
                        await bot.send_group_msg(group_id=self.target[1], message=[
                            MessageSegment.image(i)
                        ])

            await _respond(bot, event, f"[INFO] Success msg -> {self.target[0]} {self.target[1]}")
        else:
            for i in images:
                await _respond(bot, event, [ MessageSegment.image(i) ])

    async def send(self, bot: Bot, event: Event, a: list):
        for i in range(self.repeat):
            await self._send_once(bot, event, a)


    

