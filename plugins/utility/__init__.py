from nonebot import *
from nonebot.matcher import Matcher
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment, Message
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.typing import T_State
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

__plugin_meta__ = PluginMetadata(
    name="Utility",
    description="",
    usage=""".broadcast <message>
向bot加入的群组广播消息
仅限超级用户
"""
)


# friend_add = on_notice(block=True)

broadcast = on_command('broadcast', priority=90, block=True, permission=SUPERUSER)

@broadcast.handle()
async def _(bot: Bot, msg: Message = CommandArg()):
    groups = await bot.get_group_list()
    for i in groups:
        await bot.send_group_msg(group_id=i, message=msg.extract_plain_text())
    await broadcast.finish('Broadcast complete')

# @friend_add.handle()
# async def _(bot: Bot, event: FriendAddNoticeEvent):
#     await bot.set_friend_add_request(approve=True)

# @on_request('friend')
# async def _(bot: Bot, event: RequestEvent):
#     await bot.call_api('')
#     print(event.dict())