
from nonebot.adapters.onebot.v11.event import Event, PrivateMessageEvent
from nonebot.adapters.onebot.v11.bot import Bot

async def send_forward_msg(bot: Bot, event: Event, message: list):
    info = await bot.get_login_info()
    message = [
        {
            "type": "node",
            "data": {
                "name": 'nmBot',
                "uin": info.get('user_id'),
                "content": x
            }
        } for x in message]
    if isinstance(event, PrivateMessageEvent):
        await bot.call_api('send_private_forward_msg', user_id=event.get_user_id(), messages=message)
    else:
        await bot.call_api('send_group_forward_msg', group_id=event.group_id, messages=message)
