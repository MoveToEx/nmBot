from nonebot import on_command, get_driver, require, get_bot
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.plugin import PluginMetadata
from nonebot.params import Arg, CommandArg, ArgPlainText
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.helpers import Cooldown

import random
import os
import json
from time import time
from .config import Config

require('nonebot_plugin_apscheduler')

from nonebot_plugin_apscheduler import scheduler

global_config = get_driver().config
config = Config.parse_obj(global_config)


__plugin_meta__ = PluginMetadata(
    name="ICU",
    description="",
    usage=f""".icu|fb|发病 <object> 对object发病
声明：所有文本均来源于互联网，开发者仅负责收集与更改格式，其他内容与开发者无关"""
)

icu = on_command("icu", aliases={'发病', 'fb'}, priority=7, block=True)
db = []

if not config.WORKDIR.exists():
    os.makedirs(config.WORKDIR)

@icu.handle(parameterless=[Cooldown(cooldown=30, prompt='你个傻逼有完没完')])
async def fb_prep(matcher: Matcher, args: Message = CommandArg()):
    plain_text = args.extract_plain_text()
    if plain_text:
        matcher.set_arg("text", args)

@icu.got("text", prompt="你要对谁发病")
async def fb_main(param: str = ArgPlainText("text")):
    with open(config.DB_PATH, 'r', encoding='utf8') as f:
        db = json.loads(f.read())
        
    random.seed(time())
    s = random.choice(db).replace("{}", param)
    await icu.finish(s)

