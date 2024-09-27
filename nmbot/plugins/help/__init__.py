from nonebot import on_command, get_loaded_plugins
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.message import Message
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import PluginMetadata

from .utils import *

__plugin_meta__ = PluginMetadata(
    name="Help",
    description="显示帮助",
    type='application',
    usage=""".help [plugin]"""
)

help = on_command("help", priority=1, block=True)

@help.handle()
async def help_main(bot: Bot, event: Event, arg: Message = CommandArg()):
    plugins = get_loaded_plugins()
    res = []
    s = arg.extract_plain_text()
    if s:
        suc = 0
        for i in plugins:
            if not i.metadata or i.metadata.type != 'application':
                continue
            if i.metadata.name.upper() == s.upper():
                suc = 1
                await help.finish(i.metadata.usage)
        if not suc:
            await help.finish(f"Plugin {s} not found")

    for i in plugins:
        if not i.metadata or i.metadata.type != 'application':
            continue
        s = ""
        if i.metadata.name:
            s += "Plugin: " + i.metadata.name + '\n'
        if i.metadata.description:
            s += 'Description: ' + i.metadata.description + '\n'
        if i.metadata.usage:
            s += "Usage: \n" + i.metadata.usage + '\n'
        res.append(s)
    await send_forward_msg(bot, event, res)
    