from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.params import CommandArg
from nonebot import on_command, get_driver
from nonebot.plugin import PluginMetadata
from nonebot import logger, get_plugin_config
import aiohttp
import puremagic
import urllib

from .config import Config

config = get_plugin_config(Config)

__plugin_meta__ = PluginMetadata(
    name="Wolfram|Alpha",
    description="",
    usage=""".calc <text> 使用Wolfram|Alpha计算text""",
    config=Config
)

calc = on_command("calc", aliases={'计算'}, block=True)

@calc.handle()
async def calc_main(arg: Message = CommandArg()):
    arg = arg.extract_plain_text().strip()
    if not arg:
        await calc.finish("No input given")
        
    apikey = config.wolframalpha_api_key
    url = f"http://api.wolframalpha.com/v1/simple?appid={apikey}&i={urllib.parse.quote(arg)}&units=metric"
    session = aiohttp.ClientSession(trust_env=True)

    async with session.get(url) as response:
        content = await response.read()
        await session.close()
        mime = puremagic.from_string(content, mime=True)
        if mime == 'text/plain':
            await calc.finish(MessageSegment.text(content.decode()))
        elif mime.startswith('image'):
            await calc.finish(MessageSegment.image(content))
        else:
            await calc.finish('Unexpected response type: ' + mime)
