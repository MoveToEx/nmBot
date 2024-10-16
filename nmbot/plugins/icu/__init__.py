from nonebot import on_command, get_plugin_config, require

require('nonebot_plugin_alconna')

from nonebot.adapters import Message
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent
from nonebot_plugin_orm import async_scoped_session
from nonebot_plugin_alconna import on_alconna
from arclet.alconna import Alconna, Args, Arparma, Option
from sqlalchemy import select, func, delete
from aiohttp import ClientSession

from .config import Config
from .db import Entry
from .formatter import Formatter

config = get_plugin_config(Config)

__plugin_meta__ = PluginMetadata(
    name='ICU',
    description='发电机',
    usage='''.icu| .fb | .发病 | .发癫 <object: str> [-i|--id <id: int>]
.icu.new <text: str>
.icu.pull <url: str>
    Requires the response to be an array of strings. (string[])
.icu.drop

Available templates:
    {}(object) {subject} {object} {year} {month} {day} {random} {randint}
    {date_delta <x: Date> <y: Date> <unit: 'd' | 'm' | 'y' | 'min' | 's'>}
    
Date = 'now' | 'today' | `${int}/${int}/${int}`'''
)

icu = on_alconna(Alconna(
    'icu',
    Args['text', str],
    Option('-i|--id', Args['id', int])
), aliases={'fb', '发病', '发癫'}, priority=7, block=True, use_cmd_start=True)
insert = on_command(('icu', 'new'), priority=7, block=True)
remove = on_command(('icu', 'remove'), priority=7, block=True)
pull = on_command(('icu', 'pull'), priority=7, block=True)
drop = on_command(('icu', 'drop'), priority=7, block=True)

@icu.handle()
async def icu_main(session: async_scoped_session, event: GroupMessageEvent | PrivateMessageEvent, arp: Arparma):
    id = arp.query[int]('id')
    text = arp.query[str]('text')

    if text is None:
        await icu.finish('No object specified')

    stmt = select(Entry)

    if id is None:
        stmt = stmt.order_by(func.random()).limit(1)
    else:
        stmt = stmt.where(Entry.id == id)

    result = (await session.execute(stmt)).scalar_one_or_none()

    if result is None:
        await icu.finish('No entry found.')

    try:
        s = result.text.format_map(Formatter(text, event.sender.nickname))
    except Exception as e:
        await icu.finish('Failed when formatting template:\n  ' + type(e).__name__ + ': ' + str(e))

    await icu.finish(s)

@insert.handle()
async def insert_main(session: async_scoped_session, arg: Message = CommandArg()):
    text = arg.extract_plain_text().replace('{}', '{object}')

    try:
        result = text.format_map(Formatter(text, '_obj', '_sub'))
    except Exception as e:
        await insert.finish('Failed when validating template:\n  ' + type(e).__name__ + ': ' + str(e))
    
    entry = Entry(text=text)
    session.add(entry)

    await session.flush()
    await session.commit()

    await insert.finish(f'Appended 1 row (id={entry.id}) to database\nPreview: ' + result)

@remove.handle()
async def remove_main(session: async_scoped_session, arg: Message = CommandArg()):
    if not arg.extract_plain_text().isdigit():
        await remove.finish('Failed: Expected integer')

    i = int(arg.extract_plain_text())
    await session.execute(
        delete(Entry).where(Entry.id == i)
    )

    await insert.finish('Transaction completed')

@pull.handle()
async def pull_(dbsession: async_scoped_session, args: Message = CommandArg()):
    url = args.extract_plain_text()

    if not url:
        await pull.finish('Requires URL')

    async with ClientSession(trust_env=True) as session:
        async with session.get(url) as response:
            result = await response.json(content_type=None)

    try:
        assert isinstance(result, list)

        for i in result:
            assert isinstance(i, str)
    except AssertionError as e:
        await pull.finish('Failed when validating response: ' + str(e))

    result: list[str]

    for i, s in enumerate(result):
        try:
            s.replace('{}', '{object}').format_map(Formatter('_obj', '_sub'))
        except Exception as e:
            await pull.finish(f'Failed when validating template at position {i}: \n' + type(e).__name__ + ': ' + str(e))

    for s in result:
        dbsession.add(Entry(text=s.replace('{}', '{object}')))

    await dbsession.commit()

    await pull.finish(f'Appended {len(result)} entries to database.')

@drop.handle()
async def drop_(event: PrivateMessageEvent | GroupMessageEvent, session: async_scoped_session):
    await session.execute(delete(Entry))
    await session.commit()

    await drop.finish('Dropped all rows')