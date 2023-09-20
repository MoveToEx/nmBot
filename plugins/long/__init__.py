from nonebot import get_driver, on_command, get_bot
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.params import *
from nonebot.adapters.onebot.v11.helpers import MessageSegment
from nonebot.adapters.onebot.v11.event import *
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import PluginMetadata

from pil_utils import BuildImage
import imghdr
import uuid
import requests
import os
from time import time

from .config import Config
from .selector import Selector
from .database import Database
from .decorator import Decorator
from .utils import *

__plugin_meta__ = PluginMetadata(
    name="Long",
    description="",
    usage=""".l|long [selector] [decorator] 按照selector搜索龙图，并按照decorator返回结果
.long.plot|plot <id> [text] 在模板id上绘制文字text并返回结果
.long.list|ls <selector> 返回所有与selector匹配的结果
.long.plot.list|pll 显示所有可用模板
.long.stat|stat 显示统计信息
.long.upload|upload <img> [text] [#tag1] [#tag2] [...] 上传龙图，图片也可通过回复消息传入

selector的格式如下：
    text 指定在文字中搜索
    #text 指定在标签中搜索
    =text 指定UID
    其中text可用的格式如下：
        text|c(text) 查找子串
        /text/|r(text) 查找正则表达式
        e(text) 精确匹配
    多个selector以逻辑与形式结合
    当selector以!开头时，该selector的匹配结果将取反
    selector带有简单语义分析，能够解析以括号包围的空格
        
decorator的格式如下：
    :r|rand|random 随机选取一个条目（默认）
    :<index> 选取第index个条目
    :a|all 指定所有条目
    *<multipler> 重复选取并发送multipler次，若不指定则发送一次
    ><target> 将结果发送至target，若不指定则发送至调用方
    其中target的格式如下：
        u<id> QQ号为id的用户
        g<id> 群号为id的群聊
        <text> 匹配昵称或备注中带有text的用户或群聊名中带有text的群聊(不区分大小写)，当符合条件的结果不唯一时产生错误""",
    config=Config
)

global_config = get_driver().config
config = Config.parse_obj(global_config)

if not config.WORKDIR.exists():
    os.makedirs(config.WORKDIR)

images = Database(config.WORKDIR, 'images')
templates = Database(config.WORKDIR, 'templates')

long = on_command('long', aliases={'l'}, priority=7, block=True)
long_list = on_command(('long', 'list'), aliases={'ls'}, priority=7, block=True)
long_upload = on_command(('long', 'upload'), aliases={'upload'}, priority=7, block=True)
long_stat = on_command(('long', 'stat'), aliases={'stat'}, priority=7, block=True)
long_plot = on_command(('long', 'plot'), aliases={'plot'}, priority=7, block=True)
long_plot_list = on_command(('long', 'plot', 'list'), aliases={'pll'}, priority=7, block=True)
manage = on_command('manage', priority=7, block=True)

@long.handle()
async def long_main(bot: Bot, event: Event, arg: Message = CommandArg()):
    decorator, rest = Decorator.parse(arg.extract_plain_text())
    selector = Selector.parse(rest)

    res = [ images.file(x['file']) for x in selector.match(images) ]

    if decorator.repeat > config.MAX_REPEAT:
        await long.finish(f'[ERROR] Repeating more than {config.MAX_REPEAT} times is not allowed')

    if len(res) == 0:
        await long.send("No results found")
    else:
        await decorator.send(bot, event, res)

@long_list.handle()
async def list_prep(matcher: Matcher, args: Message = CommandArg()):
    plain_text = args.extract_plain_text()
    if plain_text:
        matcher.set_arg("selector", args)

@long_list.got("selector", prompt="Selector?")
async def list_main(bot: Bot, event: Event, selector: Message = Arg()):
    res = Selector.parse(selector.extract_plain_text()).match(images)

    if len(res) == 0:
        await long_list.finish("No results found")
    else:
        await send_forward_msg(bot, event, [ MessageSegment.image(images.file(x['file']).as_uri()) for x in res ])

@long_upload.handle()
async def upload_main(event: Event, args: Message = CommandArg()):
    image = None
    tags = []
    text = ""
    res = None
    filename = f'contrib_{int(time())}'
    uid = uuid.uuid4()
    image = extract_image(event)

    if not image:
        await long_upload.finish("[ERROR] No image given")

    if len(image) > 1:
        await long_upload.finish("[ERROR] Multiple images given")

    image = image[0]

    for seg in args:
        if seg.is_text():
            for s in str(seg).split():
                if s.startswith('#'):
                    tags += [ s.removeprefix('#') ]
                else:
                    text += s.strip()

    if text == "" and len(tags) == 0:
        await long_upload.send("[WARNING] no text nor tags specified. Image may be hardly reachable")

    try:
        res = requests.get(image.get('data').get('url'))
        hdr = imghdr.what("", h=res.content)
        filename += '.jpg' if hdr == 'jpeg' else '.' + hdr

        with open(images.file(filename), "wb") as f:
            f.write(res.content)

    except Exception as e:
        await long_upload.finish("[ERROR] Exception raised when saving image: " + str(e))

    images.append({
        "uid": str(uid),
        "file": filename,
        "text": text,
        "tags": tags
    })

    images.save()

    await long_upload.send(f"Success. {len(res.content)} Bytes fetched.\nUID = {uid}\nText = {text}\nTags = {tags}\nFile = {filename}")


@long_plot.handle()
async def plot_main(bot: Bot, event: Event, args: Message = CommandArg()):
    decorator, rest = Decorator.parse(args.extract_plain_text())

    a = rest.split(' ')

    if len(a) < 1:
        await long_plot.finish(f"[ERROR] At least 1 parameters required")

    t = [x for x in templates if x['id'] == a[0]]
    text = ' '.join(a[1:]) if len(a) > 1 else ""

    if not t:
        await long_plot.finish(f"[ERROR] Invalid template id {a[0]}")

    t = t[0]
    style = t.get('style', {})

    param = {
        'xy': (t['rect']['left'], t['rect']['top'], t['rect']['right'], t['rect']['bottom']),
        'text': text,
        'max_fontsize': style.get('max_fontsize', 999),
        'fill': style.get('color', '#000000'),
        'weight': style.get('weight', 'normal'),
        'stroke_fill': style.get('stroke_color', '#000000'),
        'stroke_ratio': style.get('stroke_ratio', 0)
    }

    img = BuildImage.open(templates.file(t['file'])).draw_text(**param).save_jpg()

    await decorator.send(bot, event, [ img ])


@manage.handle()
async def manage_main(args: Message = CommandArg()):
    a = args.extract_plain_text().split()
    try:
        if a[0] == 'query':
            selector = Selector.parse(' '.join(a[1:]), Decorator.PREFIX)
            res = selector.match(images)

            if len(res) == 0:
                await manage.finish("No results found")
            else:
                s = f"{len(res)} results found.\n"
                for i in res:
                    s += f"@{i['uid']}, text={i['text']}, tags={i['tags']}, file={i['file']}\n"
                await manage.send(s)
        elif a[0] == 'modify':
            selector = Selector.parse(a[1], Decorator.PREFIX)
            res = selector.match(images)
            key = a[2]
            value = ' '.join(a[3:])
            if len(res) == 0:
                await manage.send("No images found")
            else:
                for i in res:
                    if key == 'text':
                        i['text'] = value if value != '$empty' else ''
                    elif key == 'tags':
                        i['tags'] = value.split(" ,#") if value != '$empty' else []
                    else:
                        await manage.send(f"Modification of {key} is not supported")

                images.save()

                await manage.send(f"{len(res)} images modified")
        else:
            await manage.send("Unknown command")
    except Exception as e:
        await manage.send("Exception: " + str(e))

@long_plot_list.handle()
async def plot_list_main():
    s = f"Currently {len(templates)} templates available:\n"
    s += ' '.join([ i['id'] for i in templates ])
    await long_plot_list.finish(s)

@long_stat.handle()
async def stat_main():
    s = "nmBot online.\n"
    s += f"{len(images)} images, {len(templates)} templates available\n"
    await long_stat.finish(s)