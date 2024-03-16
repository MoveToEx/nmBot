from nonebot import on_command, get_plugin_config
from nonebot.adapters import Message
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import PluginMetadata

from .config import Config
from .formats import db_formats

import json
import aiohttp
import puremagic
import mimetypes

config = get_plugin_config(Config)

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
    session = aiohttp.ClientSession(trust_env=True)
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

    async with session.get(img) as response:
        raw = await response.read()
        response.close()

    mime = puremagic.from_string(raw, mime=True)
    ext = mimetypes.guess_extension(mime)

    with aiohttp.MultipartWriter('form-data') as mp:
        mp.append(raw, { 'Content-Type': mime }).set_content_disposition('form-data', name='file', filename='image' + ext)
        async with session.post('https://saucenao.com/search.php?db=999&output_type=2&api_key=' + config.saucenao_api_key) as response:
            if not response.ok:
                await sauce.finish('Error occurred while searching')
            
            result = await response.json()
            
            if int(result['header']['status']) > 0:
                await sauce.finish("SauceNAO server error. Try again later")
            
            if int(result['header']['status']) < 0:
                await sauce.finish("Client error")

            a = []
            hidden = 0
            min_similarity = float(result['header']['minimum_similarity'])

            a.append(
                [ MessageSegment.text(f'{result["header"]["short_remaining"]} requests remaining in 30s\n{result["header"]["long_remaining"]} requests remaining in 24h') ]
            )

            for i in result['results']:
                id = i['header']['index_id']
                similarity = float(i['header']['similarity'])

                if similarity < min_similarity:
                    hidden = hidden + 1
                    continue

                if db_formats.get(id):
                    async with session.get(i['header']['thumbnail']) as thumbnail:
                        a.append([ MessageSegment.image(await thumbnail.read())])
                    a.append([ MessageSegment.text('Similarity: ' + i['header']['similarity'] + '%') ])
                    a.append([ MessageSegment.text(db_formats[id].format(**i['data'])) ])
                else:
                    a.append([ MessageSegment.text(json.dumps(db_formats[id], ensure_ascii=False, indent=4))])

            if hidden:
                a.append([ MessageSegment.text(f'{hidden} images are hidden due to low similarity') ])

            await send_forward_msg(bot, event, a, 'nmBot', 1278106057)

    await session.close()

