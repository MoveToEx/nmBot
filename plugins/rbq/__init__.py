import random
import json
import asyncio
from time import time
from nonebot import get_driver, on_command
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11.helpers import Cooldown

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

__plugin_meta__ = PluginMetadata(
    name="RBQ",
    description="",
    usage=""".日[object]
可用的object格式：
    留空 从所有群成员中随机选择
    群主 指定群主
    管理 从管理员中随机选择
    群友 从所有群成员中随机选择
    群员 从非群主非管理的群成员中随机选择
    我 调用者
    QQ号
    at
    回复消息的发送者
    群成员昵称
    群成员群昵称
冷却：1min"""
)

rbq = on_command('日', aliases={'囸'}, priority=5, block=True)

prompts = {}

with open(config.WORKDIR / 'prompts.json', 'r', encoding='utf8') as f:
    prompts = json.loads(f.read())

@rbq.handle(parameterless=[Cooldown(cooldown=60, prompt='你已经射不出来任何东西了！')])
async def rbq_main(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    random.seed(time())
    target = []
    s = arg.extract_plain_text()
    
    if event.dict().get('reply'):
        target.append(event.dict().get('reply').get('sender').get('user_id'))
    else:
        for seg in arg:
            if seg.type == 'at':
                target.append(seg.data['qq'])
        if not target:
            info = await bot.get_group_member_list(group_id=event.group_id)
            if not s or s == '群友':
                target = [ random.choice(info)['user_id'] ]
            elif s == '群主':
                target = [ x['user_id'] for x in info if x['role'] == 'owner']
            elif s == '管理':
                target = [ random.choice([ x['user_id'] for x in info if x['role'] == 'admin']) ]
            elif s == '群员':
                target = [ random.choice([ x['user_id'] for x in info if x['role'] == 'member']) ]
            elif s == '我':
                target = [ event.user_id ]
            elif s.isdigit():
                if len([ x for x in info if x['user_id'] == int(s) ]):
                    target.append(s)
            else:
                target += [ x['user_id'] for x in info if x['card'] == s or x['nickname'] == s ]

    if not target:
        param = {
            'random_real': random.randint(10, 100) / 10,
            'random_integer': random.randint(10, 100),
            'target': s,
            'at_self': MessageSegment.at(event.user_id)
        }
        await rbq.finish(Message.template(random.choice(prompts['target_not_found'])).format_map(param))

    if len(target) > 1:
        param = {
            'random_real': random.randint(10, 100) / 10,
            'random_integer': random.randint(10, 100),
            'at_self': MessageSegment.at(event.user_id),
            'target_count': len(target),
            'targets': ','.join([ str(i) for i in target ])
        }
        await rbq.finish(Message.template(random.choice(prompts['multiple_targets'])).format_map(param))

    target = [ int(x) for x in target ]
    
    if str(target[0]) == str((await bot.get_login_info()).get('user_id')):
        await rbq.finish("wdnmd")
    
    if target[0] == event.user_id:
        param = {
            'random_real': random.randint(10, 100) / 10,
            'random_integer': random.randint(10, 100),
            'at_self': MessageSegment.at(event.user_id)
        }
        await rbq.send(Message([
            MessageSegment.text("咱现在帮"),
            MessageSegment.at(event.user_id),
            MessageSegment.text("涩涩！")
        ]))
        await asyncio.sleep(2)
        await rbq.finish(Message.template(random.choice(prompts['success_self'])).format_map(param))
    else:
        param = {
            'random_real': random.randint(10, 100) / 10,
            'random_integer': random.randint(10, 100),
            'at_self': MessageSegment.at(event.user_id),
            'at_target': MessageSegment.at(target[0])
        }
        await rbq.send(Message([
            MessageSegment.text("咱现在将"),
            MessageSegment.at(target[0]),
            MessageSegment.text("送给"),
            MessageSegment.at(event.user_id),
            MessageSegment.text("涩涩！")
        ]))
        await asyncio.sleep(2)
        await rbq.finish(Message.template(random.choice(prompts['success_pair'])).format_map(param))