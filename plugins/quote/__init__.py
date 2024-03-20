from nonebot import on_command, get_plugin_config
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.event import *
from nonebot.plugin import PluginMetadata
from nonebot import logger

import aiohttp
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
import numpy as np

from .config import Config
cfg = get_plugin_config(Config)

__plugin_meta__ = PluginMetadata(
    name="Quote",
    description="",
    usage=""".quote, .q 将一条消息过塑至图片，目前仅支持纯文本或单张图片消息""",
    config=Config
)

font = ImageFont.truetype('./asset/font/wqy-microhei.ttc', 64)

def breakline(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    res = []
    cur = text[0]
    for ch in text[1:]:
        if font.getbbox(cur + ch)[2] <= max_width:
            cur += ch
        else:
            res.append(cur)
            cur = ch
    res.append(cur)
    return res

def crop_avatar(img: Image.Image) -> Image.Image:
    mask = Image.new('L', img.size)

    draw = ImageDraw.Draw(mask)
    draw.pieslice(((0, 0), img.size), 0, 360, 255)

    return Image.fromarray(np.dstack((np.array(img), np.array(mask))))

def wrap_round_rect(img: Image.Image, radius: int, fill: str) -> Image.Image:
    res = Image.new('RGBA', (img.size[0] + 2 * radius, img.size[1] + 2 * radius))
    draw = ImageDraw.Draw(res)
    draw.rounded_rectangle((0, 0, *res.size), radius, fill)
    res.paste(img, (radius, radius))
    return res

def draw_text(text: str):
    text = '\n'.join(breakline(text, font, cfg.quote_max_width))
    
    res = Image.new(mode='RGB', size=(0, 0))
    draw = ImageDraw.Draw(res)

    textbox = draw.multiline_textbbox((0, 0), text, font)

    res = res.resize(textbox[2:])

    draw = ImageDraw.Draw(res)

    draw.rectangle((0, 0, *res.size), cfg.quote_background_color)
    draw.multiline_text((0, 0), text, font=font, fill=cfg.quote_foreground_color)

    return res

def pad(img: Image.Image, padding: int):
    res = Image.new(mode='RGBA', size=(img.width + padding * 2, img.height + padding * 2))

    res.paste(img, (padding, padding))

    return res

quote = on_command('quote', aliases={'q'}, priority=8, block=True)

@quote.handle()
async def quote_(event: PrivateMessageEvent | GroupMessageEvent):
    if not event.reply:
        await quote.finish('This command requires replying a message')

    session = aiohttp.ClientSession()

    reply = event.reply.message
    uid = event.reply.sender.user_id
    nickname = event.reply.sender.nickname

    content = None

    if len(reply) == 1 and reply[0].type == 'image':
        async with session.get(reply[0].data['url']) as response:
            content = Image.open(BytesIO(await response.read()))

            response.close()
    else:
        text = ''
        for seg in reply:
            if seg.type != 'text':
                await quote.finish('Unsupported message segment type: ' + seg.type)
            text += seg.data['text']
        content = draw_text(text)

    if not content:
        await quote.finish('Unexpected error')

    async with session.get('http://q1.qlogo.cn/g?b=qq&nk=' + str(uid) + '&s=640') as response:
        avatar = Image.open(BytesIO(await response.read()))
        response.close()

    await session.close()

    avatar = avatar.resize((cfg.quote_avatar_size, cfg.quote_avatar_size))

    wrapped = wrap_round_rect(content, cfg.quote_border_radius, cfg.quote_background_color)

    res = Image.new(
        mode='RGBA',
        size=(cfg.quote_avatar_size + cfg.quote_avatar_padding * 2 + wrapped.width, max(wrapped.height, avatar.height + cfg.quote_avatar_padding * 2))
    )

    res.paste(crop_avatar(avatar), (cfg.quote_avatar_padding, cfg.quote_avatar_padding))
    res.paste(wrapped, (cfg.quote_avatar_size + 2 * cfg.quote_avatar_padding, 0))

    res = pad(res, cfg.quote_padding)

    io = BytesIO()

    res.save(io, format='PNG')

    await quote.finish([MessageSegment.image(io)])
