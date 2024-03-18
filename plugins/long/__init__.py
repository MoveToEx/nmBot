from nonebot import on_command, get_plugin_config, on_message
from nonebot.config import Config as GlobalConfig
from nonebot.adapters import Message
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import PluginMetadata
from nonebot import logger

from pil_utils import BuildImage
from io import BytesIO
import aiohttp
import re
import requests
import os
import random
import seqsim
from pathlib import Path
from functional import seq

from .config import Config
from .database import Database, parse_query
from .utils import *

__plugin_meta__ = PluginMetadata(
    name="Long",
    description="",
    usage=""".l|long [text...] [#tags...] [!#exclude_tags...] [<|>|<=|>=|!=|=aggr...] 搜索图片
DISABLED: .long.plot|plot <id> [text] 在模板id上绘制文字text并返回结果
.long.list|ls <selector> 返回所有与selector匹配的结果
DISABLED: .long.plot.list|pll 显示所有可用模板
.long.stat|stat 显示统计信息
.long.upload|upload <img> [text] [#tag] [=aggr] [!] 上传图片，图片也可通过回复消息传入，加!则代表忽略相似项
.shortcut.add, .sh.add <keyword | /regex/> <post_id> 新建快龙方式
.shortcut.list, .sh.ls 列出现有的所有快龙方式
.shortcut.remove, .sh.rm <id...> 删除快龙方式
.hub.sync 将本地数据库与LONG Hub进行同步
.hub.bind [access_key] 绑定LONG Hub账户
.hub.unbind 解绑LONG Hub账户
.hub.similar|similar <image> (Not implemented yet) 查找相似图片
.hub.purge (仅限超级用户) 清空本地缓存
.hub.ping 测试与LONG Hub的HTTPS连接延迟""",
    config=Config
)

config = get_plugin_config(Config)

workdir = Path(config.data_root).absolute() / 'long'

if not workdir.exists():
    os.makedirs(workdir)

if not workdir.joinpath('post').exists():
    workdir.joinpath('post').mkdir()

db = Database()

long = on_command('long', aliases={'l'}, priority=7, block=True)
long_list = on_command(('long', 'list'), aliases={'ls'}, priority=7, block=True)
long_upload = on_command(('long', 'upload'), aliases={'upload'}, priority=7, block=True)
long_stat = on_command(('long', 'stat'), aliases={'stat'}, priority=7, block=True)
long_plot = on_command(('long', 'plot'), aliases={'plot'}, priority=7, block=True)
long_plot_list = on_command(('long', 'plot', 'list'), aliases={'pll'}, priority=7, block=True)
long_similar = on_command(('long', 'similar'), aliases={'similar'}, priority=7, block=True)
shortcut = on_message(priority=9, block=False)
shortcut_add = on_command(('shortcut', 'add'), aliases={('sh', 'add')}, priority=7, block=True)
shortcut_list = on_command(('shortcut', 'list'), aliases={('sh', 'ls')}, priority=7, block=True)
shortcut_remove = on_command(('shortcut', 'remove'), aliases={('sh', 'rm')}, priority=7, block=True)
hub_ping = on_command(('hub', 'ping'), priority=7, block=True)
hub_sync = on_command(('hub', 'sync'), priority=7, block=True)
hub_bind = on_command(('hub', 'bind'), priority=7, block=True)
hub_account = on_command(('hub', 'account'), priority=7, block=True)
hub_unbind = on_command(('hub', 'unbind'), priority=7, block=True)
hub_purge = on_command(('hub', 'purge'), priority=7, block=True)

@hub_sync.handle()
async def hub_sync_():
    await hub_sync.send('Sync started')
    
    try:
        (added, removed, modified) = await db.sync()
    except aiohttp.ClientError as e:
        await hub_sync.finish('Exception raised: ' + str(e))

    await hub_sync.finish('Success [+%d -%d M%d]' % (added, removed, modified))

@hub_bind.handle()
async def hub_bind_(event: PrivateMessageEvent | GroupMessageEvent, arg: Message = CommandArg()):
    key = arg.extract_plain_text()

    if not key:
        await hub_bind.finish('Error: No access key found')

    user = await db.validate_key(key)

    if user is None:
        await hub_bind.finish('Error: Invalid access key')

    if isinstance(event, GroupMessageEvent):
        success, data = await db.reset_key(key)

        if not success:
            await hub_bind.finish('Failed when trying to reset access key')

        await hub_bind.send('Your access key has been reset to avoid compromise')

        key = data

    db.bind(event.user_id, key)

    await hub_bind.finish('Success: ' + str(event.user_id) + ' -> ' + user)

@hub_unbind.handle()
async def hub_unbind_(event: PrivateMessageEvent | GroupMessageEvent):
    db.unbind(str(event.user_id))
    await hub_unbind.finish('Success')

@hub_account.handle()
async def hub_account_(event: PrivateMessageEvent | GroupMessageEvent):
    data = await db.account_info(event.user_id)

    if data is None:
        await hub_account.finish('Invalid key or no key found')
    
    await hub_account.finish('Account name=%s, id=%d' % (data['name'], data['id']))

@hub_purge.handle()
async def hub_purge_(event: PrivateMessageEvent | GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    uid = event.user_id

    if not uid in GlobalConfig.superusers:
        await hub_purge.finish("This command requires super user permission")
    
    if s := args.extract_plain_text():
        matcher.set_arg('confirm', s)

@hub_purge.got('confirm', prompt='Confirm? [y/N]')
async def hub_purge_confirm(confirm: str = ArgPlainText()):
    if confirm.upper() == 'Y':
        [count, size] = db.purge()
        await hub_purge.finish('Deleted %d posts, %d MiB on disk' % (count, int(size / 1024 / 1024)))
    
    await hub_purge.finish('Cancelled')
    
@hub_ping.handle()
async def hub_ping_():
    [ok, data] = await db.ping()

    if ok:
        await hub_ping.finish('Success: ' + data)
    else:
        await hub_ping.finish('Failed: ' + data)

@long.handle()
async def long_(arg: Message = CommandArg()):
    args = arg.extract_plain_text().split()
    query = parse_query(args)
    
    result = db.get(query)

    if len(result) == 0:
        await long.finish("No result found")

    text = seq(query).filter(lambda x: x.type == 'text').map(lambda x: x.value).to_list()

    if len(text) == 1:
        logger.debug(result)
        s = seq(result).map(lambda x: (x, seqsim.edit.levenshtein_dist(x.text, text[0]))).to_list()
        result = sorted(s, key=lambda x: x[1])

        best_match_diff = result[0][1]

        logger.debug(seq(result).map(lambda x: x[0].text).to_list())
        
        result = seq(result).filter(lambda x: x[1] == best_match_diff).map(lambda x: x[0]).to_list()
        
        logger.debug(seq(result).map(lambda x: x.text).to_list())
        post = random.choice(result)
    else:
        post = random.choice(result)

    with open(post.image, 'rb') as f:
        await long.finish([ MessageSegment.image(f.read()) ])

@long_list.handle()
async def long_list_(bot: Bot, event: Event, arg: Message = CommandArg()):
    args = arg.extract_plain_text().split()
    query = parse_query(args)
    
    result = db.get(query)

    if len(result) == 0:
        await long_list.finish("No result found")
    else:
        msg = []
        if len(result) > 12:
            await long_list.send(str(len(result)) + ' results found. Truncated to 12 images.')
            result = result[:12]

        for post in result:
            with open(post.image, 'rb') as f:
                msg.append(Message([
                    MessageSegment.text("ID: %s\nText: %s\nTags: %s\nAggr: %.1f\n" % (post.id, post.text, ','.join(post.tags), post.aggr)),
                    MessageSegment.image(f.read())
                ]))
        await send_forward_msg(bot, event, msg)

@shortcut_add.handle()
async def shortcut_add_(arg: Message = CommandArg()):
    args = arg.extract_plain_text().split()
    if len(args) < 2:
        await shortcut_add.finish('Error: 2 parameters required')

    if not re.match(r'^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$', args[-1]):
        await shortcut_add.finish('Error: Invalid ID format')

    type = 'match'
    pattern: str = ' '.join(args[:-1])
    post_id: str = args[-1]

    if pattern.startswith('/') and pattern.endswith('/'):
        type = 'regex'
        pattern = pattern[1:-1]
    
    pattern = pattern.replace('\\/', '/')

    if not pattern:
        await shortcut_add.finish('Error: Invalid pattern')

    [ok, data] = db.new_shortcut(type, pattern, post_id)

    if not ok:
        await shortcut_add.finish('Error: ' + data)
    
    await shortcut_add.finish('Success')

@shortcut_list.handle()
async def shortcut_list_():
    shortcut = db.list_shortcut()

    if len(shortcut) == 0:
        await shortcut_list.finish("No shortcut available")

    result = ""
    for sh in shortcut:
        result += f'#{sh.id}: ({sh.type}) {sh.pattern} -> {sh.postId}\n'
    
    await shortcut_list.finish(result)

@shortcut_remove.handle()
async def shortcut_remove_(arg: Message = CommandArg()):
    ids = arg.extract_plain_text().split()
    success = []

    if seq(ids).map(lambda x: not x.isdigit()).any():
        await shortcut_remove.finish('Error: Invalid ID')

    for id in ids:
        ok, data = db.remove_shortcut(int(id))

        if ok:
            success.append(id)
        else:
            await shortcut_remove.send('Error at #' + id + ': ' + data)
    
    await shortcut_remove.finish('Successfully removed shortcut ' + ', '.join(seq(success).map(lambda x: '#' + x).to_list()))

@shortcut.handle()
async def shortcut_(matcher: Matcher, event: PrivateMessageEvent | GroupMessageEvent):
    msg = event.get_message().extract_plain_text().strip()
    
    result = db.get_shortcut(msg)

    if len(result) == 0:
        return
    
    result = random.choice(result)
    
    matcher.stop_propagation()

    await shortcut.finish([ MessageSegment.image(result.image) ])

@long_upload.handle()
async def long_upload_(event: PrivateMessageEvent | GroupMessageEvent, args: Message = CommandArg()):
    img = extract_image(event)

    if not img:
        await long_upload.finish('Error: No image found')

    if len(img) > 1:
        await long_upload.finish('Error: Multiple images found')

    img: str = img[0].data['url']
    
    session = aiohttp.ClientSession()

    try:
        async with session.get(img) as response:
            raw = await response.read()
            response.close()
    except aiohttp.ClientError as e:
        await long_upload.finish('Failed when downloading image: ' + str(e))

    try:
        [success, data] = await db.upload(raw, args.extract_plain_text().split(), str(event.user_id))
    except aiohttp.ClientError as e:
        await long_upload.finish('Failed when uploading: ' + str(e))

    if not success:
        await long_upload.finish('Failed when uploading: ' + data)
    
    await long_upload.finish('Success, id = %s' % data['id'])

# TODO later
@long_similar.handle()
async def long_similar_(event: PrivateMessageEvent | GroupMessageEvent):

    img = extract_image(event)

    if not img:
        await long_upload.finish('Error: No image found')

    if len(img) > 1:
        await long_upload.finish('Error: Multiple images found')

    img: str = img[0].data['url']

    session = aiohttp.ClientSession()

    try:
        async with session.get(img) as response:
            raw = await response.read()
            response.close()
    except aiohttp.ClientError as e:
        await long_upload.finish('Failed when downloading image: ' + str(e))

    try:
        [ok, data] = await db.similar(raw)


    except aiohttp.ClientError as e:
        await long_upload.finish('Failed when uploading: ' + str(e))

# TODO Implement after finalizing LONG Hub template function
@long_plot.handle()
async def long_plot_(bot: Bot, event: Event, args: Message = CommandArg()):
    await long_plot.finish('disabled')
    decorator, rest = Decorator.parse(args.extract_plain_text())
    templates = hub.get_templates()

    a = rest.split(' ')

    if len(a) < 1:
        await long_plot.finish(f"[ERROR] At least 1 parameters required")

    t = [x for x in templates if x['name'] == a[0]]
    text = ' '.join(a[1:]) if len(a) > 1 else ""

    if not t:
        await long_plot.finish(f"[ERROR] Invalid template id {a[0]}")

    t = t[0]
    style = t.get('styles', {})

    raw = requests.get(t['image'])

    param = {
        'xy': (t['left'], t['top'], t['right'], t['bottom']),
        'text': text,
        'max_fontsize': style.get('max_fontsize', 999),
        'fill': style.get('color', '#000000'),
        'weight': style.get('weight', 'normal'),
        'stroke_fill': style.get('stroke_color', '#000000'),
        'stroke_ratio': style.get('stroke_ratio', 0)
    }

    img = BuildImage.open(BytesIO(raw.content)).draw_text(**param).save_jpg()

    await decorator.send(bot, event, [ img ])

@long_plot_list.handle()
async def long_plot_list_():
    await long_plot_list.finish('disabled')
    templates = hub.get_templates()
    s = f"Currently {len(templates)} templates available:\n"
    s += ' '.join([ i['name'] for i in templates ])
    await long_plot_list.finish(s)

@long_stat.handle()
async def long_stat_():
    await long_stat.finish(f"{db.size()} images in cache")