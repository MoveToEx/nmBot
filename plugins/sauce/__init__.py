from nonebot import get_driver, on_command
from nonebot.adapters import Message
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import PluginMetadata

from .config import Config
from .formats import db_formats

import json
import requests
import imghdr

global_config = get_driver().config
config = Config.parse_obj(global_config)

__plugin_meta__ = PluginMetadata(
    name="SauceNAO",
    description="",
    usage=""".sauce <image> 使用SauceNAO搜索图片""",
    config=Config
)

sauce = on_command('sauce', priority=7, block=True)


async def send_forward_msg(bot: Bot, event: Event, message: list, name: str, uid: int):
    messages = [
        {
            "type": "node",
            "data": {
                "name": name,
                "uin": uid,
                "content": x
            }
        } for x in message]
    if isinstance(event, PrivateMessageEvent):
        await bot.call_api('send_private_forward_msg', user_id=event.get_user_id(), messages=messages)
    else:
        await bot.call_api('send_group_forward_msg', group_id=event.group_id, messages=messages)


@sauce.handle()
async def sauce_main(bot: Bot, event: Event, args: Message = CommandArg()):
    img = None

    data = event.dict()
    if data.get('reply', None):
        for seg in data['reply']['message']:
            if seg.type == 'image':
                if img:
                    await sauce.finish("Multiple images specified")
                else:
                    img = seg.data['url']
    else:
        for seg in args:
            if seg.type == 'image':
                if img:
                    await sauce.finish("Multiple images specified")
                else:
                    img = seg.data['url']

    if not img:
        await sauce.finish("No image")

    res = requests.get(img)

    try:
        res = requests.post(
            'https://saucenao.com/search.php?db=999&output_type=2&api_key=' + global_config.saucenao_api_key,
            files={
                'file': ('image.' + imghdr.what('', h=res.content), res.content)
            },
            proxies=global_config.saucenao_proxy
        )
    except Exception as e:
        await sauce.finish('[ERROR] ' + str(e))

    if res.status_code != 200:
        await sauce.finish(f"[ERROR] Request returned {res.status_code}")

    s = json.loads(res.content)

    print(s)

    if int(s['header']['status']) > 0:
        sauce.finish("SauceNAO server error. Try again later")
    
    if int(s['header']['status']) < 0:
        sauce.finish("Client error")

    a = []
    hidden = 0
    min_similarity = float(s['header']['minimum_similarity'])

    a.append(
        [ MessageSegment.text(f'{s["header"]["short_remaining"]} requests remaining in 30s\n{s["header"]["long_remaining"]} requests remaining in 24h') ]
    )

    for i in s['results']:
        id = i['header']['index_id']
        similarity = float(i['header']['similarity'])

        if similarity < min_similarity:
            hidden = hidden + 1
            continue

        if db_formats.get(id):
            thumb = requests.get(i['header']['thumbnail'], proxies=config.PROXY).content
            a.append(
                [ MessageSegment.image(thumb) ]
            )
            a.append(
                [ MessageSegment.text('Similarity: ' + i['header']['similarity'] + '%') ]
            )
            a.append(
                [ MessageSegment.text(db_formats[id].format(**i['data'])) ]
            )
        else:
            a.append(
                [ MessageSegment.text(json.dumps(db_formats[id], ensure_ascii=False, indent=4))]
            )

    if hidden:
        a.append(
            [ MessageSegment.text(f'{hidden} images are hidden due to low similarity') ]
        )

    await send_forward_msg(bot, event, a, 'nmBot', 1278106057)
