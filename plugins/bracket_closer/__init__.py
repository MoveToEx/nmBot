from nonebot import get_driver, on_message
from nonebot.params import *
from nonebot.adapters.onebot.v11.event import *
from nonebot.plugin import PluginMetadata

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

closed = {
    '(': ')',
    '（': '）',
    '[': ']',
    '【': '】',
    '{': '}'
}

__plugin_meta__ = PluginMetadata(
    name="Bracket Closer",
    description="",
    usage='当消息结尾含有未闭合的括号时自动闭合',
    config=Config
)

bracket = on_message(priority=98, block=False)

@bracket.handle()
async def _(event: MessageEvent, matcher: Matcher):
    s = event.get_message().extract_plain_text()
    res = ""
    for i in s[::-1]:
        if closed.get(i, None):
            res += closed.get(i)
        else:
            break
    if res:
        matcher.stop_propagation()
        await bracket.finish(res)