from nonebot import on_message, get_plugin_config, on_command
from nonebot.params import *
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.plugin import PluginMetadata
from nonebot_plugin_orm import async_scoped_session

from .config import Config

from sqlalchemy import select, update

from .db import Enabled

config = get_plugin_config(Config)

closed = {
    '(': ')',
    '（': '）',
    '[': ']',
    '【': '】',
    '{': '}',
    '<': '>',
    '《': '》',
}

__plugin_meta__ = PluginMetadata(
    name='Bracket Pairer',
    description='',
    usage='''当消息结尾含有未闭合的括号时自动闭合
.bp.disable [groups: int[] = [event.group_id]] 禁用括号闭合
.bp.enable [groups: int[] = [event.group_id]] 启用括号闭合''',
    config=Config
)

bracket = on_message(priority=98, block=False)
bracket_enable = on_command(('bp', 'enable'), priority=12, block=True)
bracket_disable = on_command(('bp', 'disable'), priority=12, block=True)

def extract_group_id(event: GroupMessageEvent | PrivateMessageEvent, msg: Message) -> list[str]:
    raw = msg.extract_plain_text().strip()

    groups = []

    if raw:
        for id in raw.split():
            if id.isdigit():
                groups.append(id)
    elif isinstance(event, GroupMessageEvent):
        groups.append(str(event.group_id))
    
    return groups

@bracket.handle()
async def _(event: GroupMessageEvent, matcher: Matcher, session: async_scoped_session):
    s = event.get_message().extract_plain_text()

    if not s or s[-1] not in closed:
        return
    
    res = await session.execute(select(Enabled).where(Enabled.group_id == int(event.group_id)))
    pref = res.scalar_one_or_none()

    if pref is None or pref.enabled == False: 
        return
    
    res = ''
    for i in s[::-1]:
        ch = closed.get(i)
        if ch:
            res += ch
        else:
            break
    if res:
        matcher.stop_propagation()
        await bracket.finish(res)

@bracket_enable.handle()
async def bracket_enable_(event: GroupMessageEvent | PrivateMessageEvent, session: async_scoped_session, msg: Message = CommandArg()):
    groups = extract_group_id(event, msg)

    if not groups:
        await bracket_enable.finish('No valid group ID found')

    res = await session.execute(select(Enabled).where(Enabled.group_id.in_(groups)))
    for i in res.scalars():
        i.enabled = True
        groups.remove(i.group_id)

    for group in groups:
        session.add(Enabled(group_id=group, enabled=True))

    await session.commit()

    await bracket_enable.finish('Enabled bracket pairing for group ' + ','.join(groups))


@bracket_disable.handle()
async def bracket_disable_(event: GroupMessageEvent | PrivateMessageEvent, session: async_scoped_session, msg: Message = CommandArg()):
    groups = extract_group_id(event, msg)

    if not groups:
        await bracket_enable.finish('No valid group ID found')

    res = await session.execute(select(Enabled).where(Enabled.group_id.in_(groups)))
    for i in res.scalars():
        i.enabled = False
        groups.remove(i.group_id)

    for group in groups:
        session.add(Enabled(group_id=group, enabled=False))

    await session.commit()

    await bracket_enable.finish('Disabled bracket pairing for group ' + ','.join(groups))