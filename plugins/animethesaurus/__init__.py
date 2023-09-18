from nonebot_plugin_apscheduler import scheduler
from nonebot import *
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.message import Message
from nonebot.adapters.onebot.v11.event import *

import random
import os
import json
from .config import Config

require('nonebot_plugin_apscheduler')

global_config = get_driver().config
config = Config.parse_obj(global_config)


__plugin_meta__ = PluginMetadata(
    name="Anime Thesaurus",
    description="",
    usage=f"""<empty>"""
)

ats = on_message(to_me(), priority=99, block=True)
poke = on_notice()

def get_content(kw: str) -> list[str]:
    with open(config.DB_PATH, 'r', encoding='utf8') as f:
        db = json.loads(f.read())

    a = [ x for x in db if kw in x['keyword']]

    if len(a) == 0:
        a = [ x for x in db if x['keyword'][0] == '_fallback' ]

    if len(a) == 0:
        return '[WARNING] No fallback entry found'

    a = random.choice(a)

    return random.choice(a['content'])

@poke.handle()
async def _(bot: Bot, event: PokeNotifyEvent):
    self_id = await bot.get_login_info().get('user_id')
    if self_id != event.target_id:
        return
    if event.group_id:
        await bot.send_group_msg(group_id=event.group_id, message=get_content('戳'))
    else:
        await bot.send_private_msg(user_id=event.user_id, message=get_content('戳'))


@ats.handle()
async def _(event: Event):
    s = event.get_message().extract_plain_text().strip()
    
    await ats.finish(get_content(s))

