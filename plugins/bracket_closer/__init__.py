from nonebot import on_message, get_plugin_config, on_command
from nonebot.params import *
from nonebot.adapters.onebot.v11.event import *
from nonebot.plugin import PluginMetadata
from nonebot import logger

from .config import Config

from pathlib import Path
import json

config = get_plugin_config(Config)

l = Path('data/bracket_closer/list.json')

disabled: dict[str, bool] = {}

if not l.exists():
    with open(l) as f:
        f.write('{}')
        f.close()

with open(l) as f:
    disabled = json.load(f)
    f.close()

def save():
    global disabled, l

    with open(l, 'w') as f:
        f.write(json.dumps(disabled))

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
.bp.disable [group1] [group2] [...] 禁用括号闭合 若未指定群号则视为指定当前群聊
.bp.enable [group1] [group2] [...] 启用括号闭合 若未指定群号则视为指定当前群聊''',
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
async def _(event: GroupMessageEvent, matcher: Matcher):
    if disabled.get(str(event.group_id), False):
        return
    
    s = event.get_message().extract_plain_text()
    res = ''
    for i in s[::-1]:
        if closed.get(i, None):
            res += closed.get(i)
        else:
            break
    if res:
        matcher.stop_propagation()
        await bracket.finish(res)

@bracket_enable.handle()
async def bracket_enable_(event: GroupMessageEvent | PrivateMessageEvent, msg: Message = CommandArg()):
    groups = extract_group_id(event, msg)

    if not groups:
        await bracket_enable.finish('No valid group ID found')

    for group in groups:
        if disabled.get(group, False):
            disabled.pop(group)

    save()

    await bracket_enable.finish('Enabled bracket pairing for group ' + ','.join(groups))


@bracket_disable.handle()
async def bracket_disable_(event: GroupMessageEvent | PrivateMessageEvent, msg: Message = CommandArg()):
    groups = extract_group_id(event, msg)

    if not groups:
        await bracket_disable.finish('No valid group ID found')

    for group in groups:
        disabled[group] = True

    save()

    await bracket_disable.finish('Disabled bracket pairing for group ' + ','.join(groups))