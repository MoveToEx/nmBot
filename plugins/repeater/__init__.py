from nonebot import get_driver, on_message
from nonebot.adapters import Message
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import PluginMetadata

from .config import Config
from .message_hash import MessageHash

global_config = get_driver().config
config = Config.parse_obj(global_config)

__plugin_meta__ = PluginMetadata(
    name="Repeater",
    description="",
    usage=f"连续{config.REPEAT_THRESHOLD}条相同消息自动复读",
    config=Config
)

repeater = on_message(priority=99)

last_msg_hash = None
repeat_count = 1

@repeater.handle()
async def repeater_main(event: Event):
    
    if not isinstance(event, GroupMessageEvent):
        return
    
    global last_msg_hash
    global repeat_count

    msg_hash = MessageHash.hash(event.get_message())

    if msg_hash == last_msg_hash:
        repeat_count = repeat_count + 1
        if repeat_count == config.REPEAT_THRESHOLD:
            await repeater.send(event.get_message())
            repeat_count = repeat_count + 1
    else:
        repeat_count = 1
    
    last_msg_hash = msg_hash
    
