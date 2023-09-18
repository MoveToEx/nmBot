from nonebot import get_driver, on_command, get_bot, on_regex
from nonebot.matcher import Matcher
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment, Message
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.typing import T_State
from nonebot.plugin import PluginMetadata

import math
import re

from .config import Config
from .api import NCMAPI
from .format import *
from .utils import *
from .cl1p import Cl1p

__plugin_meta__ = PluginMetadata(
    name="NeteaseCloudMusic",
    description="",
    usage=""".ncm <keyword> 搜索keyword并返回首个匹配项
.ncm.search|ns <keyword> 搜索keyword并返回至多10个匹配项，等待用户选择
    使用next/prev翻页
.ncm.detail [id1, ...] 返回ID对应歌曲详细信息
.ncm.lyric [id] 获取歌曲歌词
网易云音乐链接 返回分享链接""",
    config=Config
)

global_config = get_driver().config
config = Config.parse_obj(global_config)

last_kw = ''

ncm = on_command('ncm', aliases={'网易点歌'}, priority=7, block=True)
ncm_search = on_command(('ncm', 'search'), aliases={'ns'}, priority=7, block=True)
ncm_detail = on_command(('ncm', 'detail'), priority=7, block=True)
ncm_lyric = on_command(('ncm', 'lyric'), priority=7, block=True)
link_parser = on_regex(r'https:\/\/music\.163\.com\/song\?id=(\d+)&?.*', priority=7, block=True)

api = NCMAPI()
cl1p = Cl1p(global_config.cl1p_apitoken)

@link_parser.handle()
async def parse_main(id=RegexGroup()):
    await link_parser.finish(MessageSegment.music('163', id[0]))

@ncm.handle()
async def ncm_main(args: Message = CommandArg()):
    global last_kw

    kw = args.extract_plain_text()
    if not kw:
        await ncm_search.finish("[ERROR] No keyword")

    if kw == '@last':
        kw = last_kw
    else:
        last_kw = kw
        
    try:
        res = api.search(kw)
        songs = res['songs']
    except Exception as e:
        await ncm.finish('[ERROR] ' + str(e))

    if songs:
        api.select(songs[0]['id'])
        await ncm.finish(MessageSegment.music('163', songs[0]['id']))
    else:
        await ncm.finish("No results found.")

@ncm_search.handle()
async def ns_handle(state: T_State, bot: Bot, event: Event, matcher: Matcher, args: Message = CommandArg()):
    global last_kw

    kw = args.extract_plain_text()

    if not kw:
        await ncm_search.finish("[ERROR] No keyword")

    if kw == '@last':
        kw = last_kw
    else:
        last_kw = kw

    res = api.search(kw)

    songs = res['songs']
    
    if len(songs) == 1:
        api.select(songs[0]['id'])
        await ncm_search.finish(MessageSegment.music('163', songs[0]['id']))

    state['results'] = res
    state['keyword'] = kw
    state['offset'] = 0

    await send_forward_msg(bot, event, Formatter.SearchResult.format(res, 0))

@ncm_search.got("index", prompt='Select an index')
async def ns_main(state: T_State, bot: Bot, event: Event, index: str = ArgPlainText("index")):
    if index == 'prev':
        if state['offset'] == 0:
            await ncm_search.reject('Already first 10 items. Try again')

        state['offset'] -= 10
        state['results'] = api.search(state['keyword'], state['offset'])
        await send_forward_msg(bot, event, Formatter.SearchResult.format(state['results'], state['offset']))
        await ncm_search.reject('Select an index')

    elif index == 'next':
        state['offset'] += 10
        state['results'] = api.search(state['keyword'], state['offset'])
        if not len(state['results']):
            await ncm_search.finish('No results found')
        await send_forward_msg(bot, event, Formatter.SearchResult.format(state['results'], state['offset']))
        await ncm_search.reject('Select an index')

    elif not index.isdigit():
        await ncm_search.finish("Invalid index. Exiting")

    songs = state['results']['songs']

    i = int(index)
    if i >= len(songs) or i < 0:
        await ncm_search.reject("Index out of range. Try again")

    api.select(songs[i]['id'])
    await ncm_search.finish(MessageSegment.music('163', songs[i]['id']))

@ncm_detail.handle()
async def ncm_detail_main(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    s = arg.extract_plain_text().strip()
    ids = list(filter(lambda x: x, re.split(r'\D', s)))
    results = api.detail(ids)

    msg = Formatter.Detail.format(results)

    if len(ids) <= 1:
        await ncm_detail.finish(msg[0])
    else:
        await send_forward_msg(bot, event, msg)

@ncm_lyric.handle()
async def ncm_lyric_main(arg: Message = CommandArg()):
    s = arg.extract_plain_text()
    id = int(s) if s and s.isdigit() else 0
    results = api.lyric(id)
    s = ""

    if results['lrc']['lyric']:
        s += "----------LYRIC----------\n"
        s += results['lrc']['lyric']
        s += "\n"
    
    if results['tlyric']['lyric']:
        s += "----------TRANSLATED LYRIC----------\n"
        s += results['tlyric']['lyric']
        s += "\n"
    
    if results['romalrc']['lyric']:
        s += "----------ROMAJI LYRIC----------\n"
        s += results['romalrc']['lyric']
        s += "\n"

    if results['yrc']['lyric']:
        s += "----------WORD-BY-WORD LYRIC(CONVERTED TO ELRC)----------\n"
        s += yrc_to_elrc(results['yrc']['lyric'])
        s += "\n"
        

    link = cl1p.create(s)

    await ncm_lyric.finish(f"Lyric uploaded to {link}")

