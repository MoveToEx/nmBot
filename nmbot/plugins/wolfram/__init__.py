from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.params import CommandArg
from nonebot import on_command
from nonebot.plugin import PluginMetadata
from nonebot import get_plugin_config
from aiohttp import ClientSession, ClientError, hdrs
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
    arg = arg.extract_plain_text()
    if not arg:
        await calc.finish('No input given')
        
    apikey = config.wolframalpha_api_key
    url = f"http://api.wolframalpha.com/v1/simple?appid={apikey}&i={urllib.parse.quote(arg)}&units=metric"

    async with ClientSession(trust_env=True) as session:
        try:
            async with session.get(url) as response:
                type = response.headers[hdrs.CONTENT_TYPE]
                content = await response.read()
                if type == 'text/plain':
                    await calc.finish(MessageSegment.text(content.decode()))
                elif type.startswith('image'):
                    await calc.finish(MessageSegment.image(content))
                else:
                    await calc.finish('Unexpected response type: ' + type)
        except ClientError as e:
            await calc.finish('Exception raised: ' + str(e))
