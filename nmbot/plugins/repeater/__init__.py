from nonebot import get_driver, on_message, get_plugin_config
from nonebot.params import *
from nonebot.adapters.onebot.v11.event import *
from nonebot.plugin import PluginMetadata

import random
from .config import Config
from .message_hash import hash


config = get_plugin_config(Config)

__plugin_meta__ = PluginMetadata(
    name="Repeater",
    description='Auto repeat',
    type='application',
    usage=f"连续{config.repeater_threshold}条相同消息自动复读",
)

repeater = on_message(priority=99)
self_repeat_responses = [
    '你叫你妈呢'
]

class Record:
    def __init__(self, hash: str, uid: int):
        self.hash = hash
        self.count = 1
        self.accounts = set([ uid ])
    
    def increment(self, uid: int):
        self.count += 1
        self.accounts.add(uid)
    
    def count_users(self):
        return len(self.accounts)


data: dict[int, Record] = {}

@repeater.handle()
async def _(event: GroupMessageEvent):
    global data

    msg_hash = await hash(event.get_message())

    obj = data.get(event.group_id)

    if not obj:
        data[event.group_id] = Record(msg_hash, event.user_id)
    elif msg_hash == obj.hash:
        obj.increment(event.user_id)
        if obj.count == config.repeater_threshold:
            if obj.count_users() == 1:
                await repeater.send(random.choice(self_repeat_responses))
            else:
                await repeater.send(event.get_message())
    else:
        data[event.group_id] = Record(msg_hash, event.user_id)
    
    
