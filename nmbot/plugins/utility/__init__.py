from nonebot import on_command
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name='Utility',
    description='Whatever',
    type='application',
    usage='''.ping'''
)

ping = on_command('ping', priority=1, block=True)

@ping.handle()
async def _():
    await ping.finish('pong')
