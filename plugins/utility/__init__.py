from nonebot import *
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import Message
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER

__plugin_meta__ = PluginMetadata(
    name="Utility",
    description="",
    usage=""".broadcast <message>
    向bot加入的群组广播消息
    仅限超级用户
.ping
    用于检测bot状态
"""
)


friend_add = on_notice(block=True)

broadcast = on_command('broadcast', priority=90, block=True, permission=SUPERUSER)
ping = on_command('ping', priority=1, block=True)

@broadcast.handle()
async def _(bot: Bot, msg: Message = CommandArg()):
    groups = set([ x['group_id'] for x in await bot.get_group_list() ])
    for i in groups:
        await bot.send_group_msg(group_id=i, message=msg.extract_plain_text())
    await broadcast.finish('Broadcast complete')

@ping.handle()
async def _():
    await ping.finish('pong')

@friend_add.handle()
async def _(bot: Bot, event: FriendAddNoticeEvent):
    await bot.set_friend_add_request(approve=True)