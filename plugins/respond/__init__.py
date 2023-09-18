from nonebot import *
from nonebot.adapters import Message
from nonebot.params import *
from nonebot.rule import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.event import *

import os
import random

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

enabled = {
    "摸鱼",
    "摸锦鲤",
    "大展宏兔",
    "牛气冲天",
    "牛转钱坤",
    "喵喵",
    "汪汪",
    "无眼笑",
    "菜汪",
    "元宝",
    "牛啊",
    "胖三斤",
    "头秃",
    "吃瓜",
    "哦",
    "请",
    "睁眼",
    "期待",
    "拜谢",
    "崇拜",
    "豹富",
    "我酸了",
    "虎虎生威",
    "酸Q",
    "我想开了",
    "你真棒棒",
    "我方了",
    "变形",
    "大怨种",
    "比心",
    "庆祝",
    "吃糖"
}

# resp = on_command("_unused", aliases=enabled, priority=7, block=True)
resp = on_message(priority=10, block=False)

@resp.handle()
async def _(matcher: Matcher, msg: Message = EventMessage()):
    return
    if len(msg) < 1:
        return
    
    if msg[0].type == 'face':
        pass

    ls = [ config.IMAGES_PATH / s for s in os.listdir(config.IMAGES_PATH) ]
    img = random.choice(ls).as_uri()
    await resp.finish(MessageSegment.image(img))
