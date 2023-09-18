from nonebot.adapters import Bot, Event, Message
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.params import CommandArg
from nonebot.matcher import Matcher
from nonebot import on_command, get_driver
from nonebot.plugin import PluginMetadata
import urllib
import requests

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

__plugin_meta__ = PluginMetadata(
    name="Wolfram|Alpha",
    description="",
    usage=""".calc <text> 使用Wolfram|Alpha计算text""",
    config=Config
)

calc = on_command("calc", aliases={'计算'}, block=True)

def get_calc(question: str):
    apikey = global_config.wolframalpha_api_key
    url = f"http://api.wolframalpha.com/v1/simple?appid={apikey}&i={urllib.parse.quote(question)}&units=metric"
    res = requests.get(url=url, proxies=global_config.wolframalpha_proxy)
    return res.content

@calc.handle()
async def calc_main(arg: Message = CommandArg()):
    try:
        arg = arg.extract_plain_text().strip()
        if not arg:
            await calc.finish("No input given")
        result = get_calc(arg)
        await calc.send(MessageSegment.image(result))
    except Exception as e:
        await calc.send(f"[ERROR] {str(e)}")
