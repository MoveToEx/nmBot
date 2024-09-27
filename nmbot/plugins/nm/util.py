from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.console.event import MessageEvent

def get_object(event: GroupMessageEvent | PrivateMessageEvent) -> tuple[str, int]:
    if isinstance(event, GroupMessageEvent):
        return ['group', event.group_id]
    elif isinstance(event, PrivateMessageEvent):
        return ['user', event.user_id]
    else:
        return ['user', 1]