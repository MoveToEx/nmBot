from nonebot import get_driver, on_message
from nonebot.params import *
from nonebot.adapters.onebot.v11.event import *
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

data = {}

@repeater.handle()
async def _(event: GroupMessageEvent):
    global data

    msg_hash = MessageHash.hash(event.get_message())

    if not data.get(event.group_id):
        data[event.group_id] = {
            'hash': msg_hash,
            'count': 1
        }
    elif msg_hash == data[event.group_id]['hash']:
        data[event.group_id]['count'] += 1
        if data[event.group_id]['count'] == config.REPEAT_THRESHOLD:
            await repeater.send(event.get_message())
            data[event.group_id]['count'] += 1
    else:
        data[event.group_id]['count'] = 1
    
    data[event.group_id]['hash'] = msg_hash
    
