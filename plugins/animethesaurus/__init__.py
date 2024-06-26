from nonebot import *
from nonebot.params import *
from nonebot.rule import to_me
from nonebot.plugin import PluginMetadata
from nonebot.config import Config
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import *

from pathlib import Path
import random
import json
from .config import Config

require('nonebot_plugin_apscheduler')

config = get_plugin_config(Config)

__plugin_meta__ = PluginMetadata(
    name="Anime Thesaurus",
    description="",
    usage=f"""<empty>"""
)

workdir = Path(config.data_root).absolute() / 'animethesaurus'
db_path = workdir / 'data.json'

if not workdir.exists():
    os.makedirs(workdir)

if not db_path.exists():
    with open(db_path, 'w') as f:
        f.write('[]')
        f.close()

ats = on_message(rule=to_me(), priority=99)

with open(db_path, 'r', encoding='utf8') as f:
    db = json.loads(f.read())

def get_content(kw: str) -> list[str]:
    a = [ x for x in db if kw in x['keyword']]

    if len(a) == 0:
        return None

    a = random.choice(a)

    return random.choice(a['content'])


@ats.handle()
async def _(matcher: Matcher, event: Event):
    s = event.get_message().extract_plain_text().strip()

    result = get_content(s)

    logger.debug(result)

    if result == None:
        return
    
    matcher.stop_propagation()
    await ats.finish(get_content(s))

