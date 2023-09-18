from nonebot import *
from nonebot.matcher import Matcher
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment, Message
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.typing import T_State
from nonebot.plugin import PluginMetadata

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

# friend_add = on_notice(block=True)

# @friend_add.handle()
# async def _(bot: Bot, event: FriendAddNoticeEvent):
#     await bot.set_friend_add_request(approve=True)

# @on_request('friend')
# async def _(bot: Bot, event: RequestEvent):
#     await bot.call_api('')
#     print(event.dict())