from nonebot import get_plugin_config, on_startswith, on_command, require

require('nonebot_plugin_datastore')

from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg, Depends
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11.message import Message
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent

import google.generativeai as genai
from functional import seq
from sqlalchemy.ext.asyncio.session import AsyncSession
import re
from sqlalchemy import select
from nonebot_plugin_datastore import get_session

from .config import Config
from .db import Setting

INSTRUCTIONS = {
    'default': "You are a chat bot named nmBot. You're designed to simulate average human behaviour in chatting scenarios. Therefore, you should behave exactly in the way that a human will do. When replying, do not use Markdown; use plain text instead. You should respond to all messages in simplified Chinese.",
    'catgirl': "You are a chat bot named nmBot. You're designed to provide amusing content, so you need to be less serious in most conditions. Also, users may expect that you use the tone of an adorable catgirl to reply to their messages. When replying, do not use Markdown; use plain text instead. Using emojis is encouraged. You should respond to all messages in simplified Chinese.",
    'negative': "You are a chat bot named nmBot. You're designed to make negative responses to users' messages in a group chat. No matter what the user may talk about, all you need to do is simply replying against them, in a violent and disapproving tone. Using dirty words is highly recommended. When replying, do not use Markdown; use plain text instead. Using emojis to strengthen your tone is preferred. You should respond to all messages in simplified Chinese."
}

__plugin_meta__ = PluginMetadata(
    name="Gemini",
    description="",
    usage=f""".nm.set <name> [<u|g><id>...] 切换 System instruction 为 name。可用的名称有：{','.join(['disabled'] + list(INSTRUCTIONS.keys()))}
nm <content> 与 Gemini 对话""",
    config=Config,
)

config = get_plugin_config(Config)
genai.configure(api_key = config.gemini_api_key)

mode = 'default'
enabled = {}

nm = on_startswith('nm', priority=11, block=False)
nm_set = on_command(('nm', 'set'), priority=11, block=True)

@nm_set.handle()
async def nm_set_(event: GroupMessageEvent | PrivateMessageEvent, arg: Message = CommandArg(), session: AsyncSession = Depends(get_session)):
    targets = []
    args = arg.extract_plain_text().split(' ')

    if len(args) < 1:
        await nm_set.finish("At least 1 parameter is required")

    mode = args[0]

    if mode not in INSTRUCTIONS.keys() and mode != 'disabled':
        await nm_set.finish("Invalid mode " + mode)

    if len(args) == 1:
        if isinstance(event, GroupMessageEvent):
            targets.append(('group', event.group_id))
        else:
            targets.append(('user', event.user_id))

    for target in args[1:]:
        result = re.match(r'([ug]{1})(\d+)', target)

        if result is None:
            await nm_set.finish('Invalid target ' + target)

        if result.group(1) == 'u':
            targets.append(('user', int(result.group(2))))
        elif result.group(1) == 'g':
            targets.append(('group', int(result.group(2))))

    for (typ, id) in targets:
        stmt = select(Setting).where(Setting.object_type == typ, Setting.object_id == id)
        obj = await session.execute(stmt)
        scalar = obj.scalar_one_or_none()

        if scalar is None:
            session.add(Setting(object_type=typ, object_id=id, mode=mode))
        else:
            scalar.mode = mode
            
    await session.commit()

    await nm_set.finish('Success')
    

@nm.handle()
async def gemini_(matcher: Matcher, event: GroupMessageEvent | PrivateMessageEvent, session: AsyncSession = Depends(get_session)):
    object_type = 'group' if isinstance(event, GroupMessageEvent) else 'user'
    
    if isinstance(event, GroupMessageEvent):
        stmt = select(Setting).where(Setting.object_id == event.group_id, Setting.object_type == object_type)
    elif isinstance(event, PrivateMessageEvent):
        stmt = select(Setting).where(Setting.object_id == event.user_id, Setting.object_type == object_type)

    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting is None or setting.mode == 'disabled':
        return

    matcher.stop_propagation()

    model = genai.GenerativeModel(
        model_name=config.gemini_model,
        system_instruction=INSTRUCTIONS[setting.mode]
    )

    prompt = event.get_message().extract_plain_text()

    if prompt.startswith('nm '):
        prompt = prompt.removeprefix('nm ')

    try:
        response = await model.generate_content_async(
            prompt,
            safety_settings={
                'SEXUALLY_EXPLICIT': 'block_none',
                'HARASSMENT': 'block_none',
                'HATE_SPEECH': 'block_none',
            }
        )
    except Exception as e:
        await nm.finish(str(e))

    try:
        response.text
    except:
        await nm.finish('Error occurred when accessing text field. Check your safety settings.')

    await nm.finish(response.text)
