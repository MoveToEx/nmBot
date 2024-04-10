from nonebot import get_plugin_config, on_startswith
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11.event import Event, GroupMessageEvent, PrivateMessageEvent

from .config import Config

import google.generativeai as genai

__plugin_meta__ = PluginMetadata(
    name="Gemini",
    description="",
    usage="nm <content> 与 Gemini 对话",
    config=Config,
)

INSTRUCTION = "You are a chatbot named nmBot. You're designed to provide amusing content, so you need to be less serious in most conditions. Also, users may expect that you use an adorable or cute tone to reply to their messages. Sometimes users may ask you academic questions in a less amusing manner; in such cases, you need to answer with brief words and try to clarify your answer with as few words as possible. When replying, do not use Markdown, but use plain text instead. Using emojis is also accepted."

config = get_plugin_config(Config)

genai.configure(api_key = config.gemini_api_key)

model = genai.GenerativeModel(
    model_name='gemini-1.5-pro-latest',
    system_instruction=INSTRUCTION
)

gemini = on_startswith('nm', priority=11, block=True)

@gemini.handle()
async def gemini_(event: GroupMessageEvent | PrivateMessageEvent):
    prompt = event.get_message().extract_plain_text()

    if prompt.startswith('nm '):
        prompt.removeprefix('nm ')

    try:
        response = await model.generate_content_async(
            prompt,
            safety_settings={
                'SEXUALLY_EXPLICIT': 'block_none',
                'HARASSMENT': 'block_none',
                'HATE_SPEECH': 'block_medium_and_above',
            }
        )
    except Exception as e:
        await gemini.finish(str(e))

    try:
        response.text
    except:
        await gemini.finish('Error occurred.')

    await gemini.finish(response.text)
