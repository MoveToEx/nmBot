from nonebot_plugin_apscheduler import scheduler
from nonebot import *
from nonebot.plugin import PluginMetadata
from nonebot.log import logger

import json
import os
import requests
from .config import Config

require('nonebot_plugin_apscheduler')


__plugin_meta__ = PluginMetadata(
    name="Github Sync",
    description="",
    usage=f""".ghsync 同步repo"""
)

global_config = get_driver().config
config = Config.parse_obj(global_config)

ghsync = on_command('ghsync', priority=7, block=True)

if not config.WORKDIR.exists():
    os.makedirs(config.WORKDIR)

if not config.DB_PATH.exists():
    with open(config.DB_PATH, 'w', encoding='utf8') as f:
        f.write('[]')


@scheduler.scheduled_job("cron", hour="*", id="gh_sync", misfire_grace_time=60)
async def _() -> list:
    info = []
    with open(config.DB_PATH, 'r', encoding='utf8') as f:
        commit = json.loads(f.read())

    for repo in config.REPO:
        try:
            res = requests.get(
                repo['api'], proxies=global_config.github_proxy).content
            res = json.loads(res)
        except Exception as e:
            info.append((repo['name'], 'failed: ' + str(e)))
            logger.warning(f"Unable to sync repo {repo['name']}: {str(e)}")
            continue

        if not res.get('sha'):
            info.append((repo['name'], 'invalid response'))
            logger.warning(
                f"Invalid response. API limit may have been reached")
            continue

        if res['sha'] == commit.get(repo['api'], None):
            info.append((repo['name'], 'up-to-date'))
            logger.info(f"{repo['name']} already up to date")
            continue

        try:
            content = requests.get(
                res['download_url'], proxies=global_config.github_proxy)
        except Exception as e:
            info.append((repo['name'], 'failed: ' + str(e)))
            logger.warning(f"Unable to sync repo {repo['name']}: {str(e)}")
            continue

        with open(repo['file'], 'wb') as f:
            f.write(content.content)

        info.append(
            (repo['name'], f"{commit.get(repo['api'], '000000')[:6]} -> {res['sha'][:6]}"))
        logger.info(
            f"Successfully updated {repo['name']}: {commit.get(repo['api'], '000000')[:6]} -> {res['sha'][:6]}")

        commit.update({repo['api']: res['sha']})

    with open(config.DB_PATH, 'w', encoding='utf8') as f:
        f.write(json.dumps(commit, ensure_ascii=False, indent=4))

    return info


@ghsync.handle()
async def sync(bot: Bot):
    res = await _()
    s = ""
    for i in res:
        s += f"[INFO] ghsync | {i[0]} | {i[1]}\n"
    await ghsync.finish(s)
