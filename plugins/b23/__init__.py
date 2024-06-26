from nonebot import on_message, get_plugin_config
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import *

import requests
import re
from bs4 import BeautifulSoup

b23 = on_message(priority=90, block=False)

# TODO Broken. Fix later

@b23.handle()
async def _(matcher: Matcher, msg: Message = EventMessage()):
    if msg[0].type == 'json':
        data = msg[0].data.get('data')

        if r := re.search(r'https?:\\/\\/b23\.tv\\/[A-Za-z0-9]+', data):
            matcher.stop_propagation()
            slk = r.group(0).replace('\\', '')
        elif r := re.search(r'https?:\\/\\/www\.bilibili\.com\\/video\\/BV[A-Za-z0-9]+', data):
            matcher.stop_propagation()
            await b23.finish('Direct link: ' + r.group(0).replace('\\', ''))
        else:
            return

        res = requests.get(slk)
        bs = BeautifulSoup(res.text, 'html.parser')
        link = bs.select_one('meta[itemprop="url"]').attrs['content']
        await b23.finish('Direct link: ' + link)
