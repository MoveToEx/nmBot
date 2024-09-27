from nonebot import on_command, get_plugin_config, on_message, require, on_notice

require('nonebot_plugin_alconna')
require('nonebot_plugin_apscheduler')

from nonebot_plugin_orm import async_scoped_session, get_scoped_session
from nonebot_plugin_alconna import on_alconna
from nonebot_plugin_apscheduler import scheduler

from nonebot.config import Config as GlobalConfig
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.message import MessageSegment, Message
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.console import MessageEvent
from nonebot.plugin import PluginMetadata
from nonebot.matcher import Matcher
from nonebot import logger

from arclet.alconna import Args, Alconna, Option, Arparma, MultiVar, store_true
import re
import random
import seqsim
from functional import seq
from typing import Literal

from .core import Core
from .utils import extract_image, fetch, send_forward_msg
from .config import Config

client = Core()

__plugin_meta__ = PluginMetadata(
    name="Long",
    description="龙",
    type='application',
    usage='''.l | .long [<filters: string | `#${string}`...>]
.l.search
        [--id <exact_id: string>]
        [--id-regex <pattern: RegExp>] 
        [-t|--text <pattern: string>] 
        [-et|--text-exclude <pattern: string>] 
        [-rt|--text-regex <pattern: RegExp>] 
        [-g|--tag <tag_name: string>] 
        [-eg|--tag-exclude <tag_name: string>] 
        [-r|--rating <rating: 'none' | 'moderate' | 'violent'>] 
        [--range [start: number][':'][end: number]]
    Requires at least one condition

.l.upload | 
        [-w|--text <text: string>] 
        [-t|--tag <tags...: string[]>] 
        [-r|--rating <rating: 'none' | 'moderate' | 'violent'>]
        [-f|--force]

.sh.add | .shortcut.add
        <post_id: UUID>
        <pattern: string | RegExp>
        [--type type: 'match' | 'regex' = pattern like '/%/' ? 'regex' : 'match']
.sh.rm | .shortcut.remove
        [-i|--id <id: int>]
        [-m|--if-matches <pattern: string>]
    Requires exactly one of id and pattern
'''
)

def is_poke(bot: Bot, event: Event) -> bool:
    return event.notice_type == 'notify' and event.sub_type == 'poke'

poke = on_notice(is_poke, priority=7, block=True)
long = on_command('long', aliases={'l'}, priority=8, block=True)
long_search = on_alconna(Alconna(
    '.l.search',
    Option('--id', Args['id', MultiVar(str)]),
    Option('--id-regex', Args['id_regex', MultiVar(str)]),
    Option('-t|--text', Args['text_include', MultiVar(str)]),
    Option('-et|--text-exclude', Args['text_exclude', MultiVar(str)]),
    Option('-rt|--text-regex', Args['text_regex', MultiVar(str)]),
    Option('-g|--tag', Args['tag_include', MultiVar(str)]),
    Option('-eg|--tag-exclude', Args['tag_exclude', MultiVar(str)]),
    Option('-r|--rating', Args['rating', MultiVar(str)]),
    Option('--range', Args['range', r'rep:(\d*)(:?)(\d*)']),
), priority=7, block=True)
long_upload = on_alconna(Alconna(
    '.l.upload',
    Option('-w|--text', Args['text', str], default=''),
    Option('-t|--tag', Args['tag', MultiVar(str)], default=['tagme']),
    Option('-r|--rating', Args['rating', Literal['n', 'm', 'v', 'none', 'moderate', 'violent']], default='none'),
    Option('-f|--force', default=False, action=store_true),
), aliases={'upload'}, priority=7, block=True)

shortcut = on_message(priority=9, block=False)
shortcut_add = on_alconna(Alconna(
    '.sh.add',
    Args['id', str],
    Args['pattern', str],
    Option('--type', Args['type', Literal['match', 'regex']])
), aliases={('shortcut', 'add')}, priority=7, block=True)
shortcut_list = on_alconna(Alconna(
    '.sh.ls',
    Option('--group', Args['group', str]),
    Option('--id', Args['id', int]),
    Option('--if-matches', Args['matches', str]),
), aliases={('shortcut', 'add')}, priority=7, block=True)
shortcut_remove = on_alconna(Alconna(
    '.sh.rm',
    Option('-i|--id', Args['id', int]),
    Option('-m|--if-matches', Args['matches', str])
), aliases={('shortcut', 'remove')}, priority=7, block=True)

hub_ping = on_command(('hub', 'ping'), priority=7, block=True)
hub_sync = on_command(('hub', 'sync'), priority=7, block=True)
hub_bind = on_command(('hub', 'bind'), priority=7, block=True)
hub_account = on_command(('hub', 'account'), priority=7, block=True)
hub_unbind = on_command(('hub', 'unbind'), priority=7, block=True)
hub_purge = on_command(('hub', 'purge'), priority=7, block=True)

@long.handle()
async def long_(event: GroupMessageEvent | PrivateMessageEvent, session: async_scoped_session, args: Message = CommandArg()):
    tags: list[str] = []
    text: list[str] = []

    for i in args.extract_plain_text().split():
        if i.startswith('#'):
            tags.append(i.removeprefix('#'))
        else:
            text.append(i)

    if not tags and not text:
        post = await client.rand(session)

        if post:
            await long.finish(MessageSegment.image(client.dir_post(post)))

    posts = await client.get(session, text, tags)

    if len(posts) == 0:
        await long.finish('No result found')

    if len(tags) == 0 and len(text) == 1:
        result = min(posts, key=lambda x: seqsim.edit.levenshtein_dist(x.text, text[0]))
    else:
        result = random.choice(posts)

    await long.finish(MessageSegment.image(client.dir_post(result)))

@poke.handle()
async def poke_(session: async_scoped_session):
    post = await client.rand(session)

    if post:
        await poke.finish(MessageSegment.image(client.dir_post(post)))


@long_search.handle()
async def long_search_(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent, params: Arparma, session: async_scoped_session):
    rg = params.query[re.Match]('range')
    start = 0
    end = 12

    if rg:
        x, y, z = rg.groups()
        if y:
            if x and z:
                start = int(x)
                end = int(z)
            elif x:
                start = int(x)
                end = start + 12
            elif z:
                end = int(z)
                start = max(0, end - 12)
        elif x:
            start = end = int(x)

    result = await client.search(session, **params.all_matched_args)

    await send_forward_msg(bot, event, seq(result).slice(start, end).map(lambda i: Message([
        MessageSegment.text("ID: %s\nText: %s\nTags: %s\nRating: %s\n" % (i.id, i.text, i.tags, i.rating)),
        MessageSegment.image(client.dir_post(i.image))
    ])))


@long_upload.handle()
async def long_upload_(event: GroupMessageEvent | PrivateMessageEvent, params: Arparma, session: async_scoped_session):
    rating_abbr = {
        'n': 'none',
        'm': 'moderate',
        'v': 'violent'
    }
    text = params.query[str]('text')
    tags = params.query[list[str]]('tag')
    rating = params.query[str]('rating')
    force = params.query[bool]('force.value')

    if rating in rating_abbr:
        rating = rating_abbr[rating]

    logger.debug('extracing image')
    image = extract_image(event)

    if len(image) == 0:
        await long_upload.finish('No image found')
    elif len(image) > 1:
        await long_upload.finish('Multiple image found')

    image = image[0]

    data = await fetch(image)

    await long_upload.send(f'''Metadata:
    Text: {text if text else '(no text)'}
    Tags: {' '.join(tags)}
    Rating: {rating}
    Image Size: {len(data) / 1024:.2f} KiB
Uploading...''')

    try:
        result = await client.upload(str(event.user_id), session, data, text, tags, rating, force)
    except Exception as e:
        await long_upload.finish(str(e))

    await long_upload.send(f'Success: {result['id']}')


@shortcut.handle()
async def shortcut_(event: GroupMessageEvent, matcher: Matcher, session: async_scoped_session):
    msg = event.get_message().extract_plain_text()
    posts = await client.get_shortcut(session, msg, event.group_id)

    if posts:
        matcher.stop_propagation()

        result = random.choice(posts)
        await shortcut.finish(MessageSegment.image(client.dir_post(result.image)))

@shortcut_list.handle()
async def shortcut_list_(event: GroupMessageEvent | PrivateMessageEvent, params: Arparma, session: async_scoped_session):
    pass

@shortcut_add.handle()
async def shortcut_add_(event: GroupMessageEvent, params: Arparma, session: async_scoped_session):
    post_id = params.query[str]('id')
    pattern = params.query[str]('pattern')
    type = params.query[Literal['match', 'regex']]('type')

    if type is None:
        if pattern.startswith('/') and pattern.endswith('/'):
            pattern = pattern[1:-1]
            type = 'regex'
        else:
            type = 'match'
    
    try:
        await client.add_shortcut(session, type, pattern, str(event.group_id), post_id)
        await session.commit()
    except Exception as e:
        await shortcut_add.finish('Failed: ' + str(e))


    await shortcut_add.finish('Success: (%s) %s -> %s for %d' % (type, pattern, post_id, event.group_id))

@shortcut_remove.handle()
async def shortcut_remove_(event: GroupMessageEvent, params: Arparma, session: async_scoped_session):
    id = params.query[int]('id')
    kw = params.query[str]('matches')

    if id and kw:
        await shortcut_remove.finish('Failed: --id and --if-matches should not be specified at the same time')

    if id:
        await client.remove_shortcut_by_id(session, id)
    elif kw:
        await client.remove_shortcut_if_matches(session, event.group_id, kw)

    await session.commit()

    await shortcut_remove.finish('Completed')

@hub_bind.handle()
async def hub_bind_(event: GroupMessageEvent | PrivateMessageEvent, session: async_scoped_session, arg: Message = CommandArg()):
    key = arg.extract_plain_text()
    try:
        if isinstance(event, GroupMessageEvent):
            result = await client.bind(session, str(event.user_id), key, True)
        elif isinstance(event, PrivateMessageEvent):
            result = await client.bind(session, str(event.user_id), key)
    except Exception as e:
        await hub_bind.finish('Failed: ' + str(e))

    if result is None:
        await hub_bind.finish('Invalid access key')

    answer = f'Success: {event.user_id} -> {result['name']} (id={result['id']})'

    if isinstance(event, GroupMessageEvent):
        answer += '\nYour access key has been reset'

    await session.commit()

    await hub_bind.finish(answer)

@hub_unbind.handle()
async def hub_unbind_(event: GroupMessageEvent | PrivateMessageEvent, session: async_scoped_session):
    await client.unbind(session, str(event.user_id))
    await session.commit()

    await hub_unbind.finish('Success')

@hub_account.handle()
async def hub_account_(event: GroupMessageEvent | PrivateMessageEvent, session: async_scoped_session):
    try:
        result = await client.get_binding(session, str(event.user_id))
    except Exception as e:
        await hub_account.finish('Failed: ' + str(e))

    if result is None:
        await hub_account.finish('No valid binding found')
    
    answer = f'Account binding of user {event.user_id}:'

    answer += f'\tID: {result['id']}'
    answer += f'\tUsername: {result['name']}'
    answer += f'\tAccess key: {result['accessKey'][:2]}*****{result['accessKey'][-2:]}'

    await hub_account.finish(answer)


@hub_sync.handle()
async def hub_sync_(event: GroupMessageEvent | PrivateMessageEvent, session: async_scoped_session):
    await hub_sync.send('Initiating synchronization...')

    try:
        await client.sync(session)
    except Exception as e:
        await hub_sync.finish(str(e))

    await session.commit()

    await hub_sync.finish('Success')

@scheduler.scheduled_job('cron', hour='*/6', id='sync')
async def auto_sync():
    session = get_scoped_session()

    try:
        await client.sync(session)
    except Exception:
        pass

    await session.commit()