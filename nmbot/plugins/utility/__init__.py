from nonebot import on_command, on_request, get_plugin_config
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot, RequestEvent, Message, PrivateMessageEvent, GroupMessageEvent, MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select, update
from json import dumps

from .db import GroupInvitation, InvitationState
from .config import Config

config = get_plugin_config(Config)

__plugin_meta__ = PluginMetadata(
    name='Utility',
    description='Misc.',
    type='application',
    usage='''.ping 测试bot连通性
.dump (回复消息) 查看回复消息对应的消息段代码'''
)

def is_group_invitation(bot: Bot, event: RequestEvent):
    return event.request_type == 'group' and event.sub_type == 'invite'

ping = on_command('ping', priority=1, block=True)
dump = on_command('dump', priority=1, block=True)
group_invitation = on_request(is_group_invitation, priority=1, block=True)
group_invitation_handler = on_command('group_inv', priority=2, block=True, permission=SUPERUSER)

@ping.handle()
async def ping_():
    await ping.finish('pong')

@dump.handle()
async def dump_(event: GroupMessageEvent | PrivateMessageEvent):
    if event.reply is None:
        await dump.finish('This command requires replying a message')
    
    result = []

    for i, message in enumerate(event.reply.message):
        result.append(f'Segment[{i}] of type \'{message.type}\':')
        result.append(dumps(message.data, indent=4, ensure_ascii=False))
    
    await dump.finish('\n'.join(result))

@group_invitation.handle()
async def group_invitation_(bot: Bot, event: RequestEvent, session: async_scoped_session):
    if int(event.user_id) == config.controller:
        await bot.call_api('set_group_add_request', flag=event.flag, sub_type='invite', approve=True)
        await bot.send_private_msg(user_id=event.user_id, message="Accepted invitation")

    result = await bot.send_private_msg(user_id=config.controller, message=f'''Received group invitation from {event.user_id}\nGroup ID: {event.group_id}\nReply with .group_inv <accept: bool> to respond''')

    session.add(GroupInvitation(inviter_id=event.user_id, message_id=result.get('message_id'), flag=event.flag, state=InvitationState.valid))
    await session.commit()

@group_invitation_handler.handle()
async def group_invitation_handler_(bot: Bot, event: PrivateMessageEvent, session: async_scoped_session, msg: Message = CommandArg()):
    if not event.reply:
        await group_invitation_handler.finish('This command requires replying a message')

    result = await session.execute(
        select(GroupInvitation)
        .where(GroupInvitation.message_id == event.reply.message_id, GroupInvitation.state == InvitationState.valid)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        await group_invitation_handler.finish('No matching invitation found. Try again')

    flag = invitation.flag
    opt = msg.extract_plain_text().upper()

    if opt not in ['Y', 'N']:
        await group_invitation_handler.finish('Unknown option. Try again')
    
    await bot.call_api('set_group_add_request', flag=flag, sub_type='invite', approve=(opt == 'Y'))

    invitation.state = InvitationState.accepted if opt == 'Y' else InvitationState.denied

    await session.execute(
        update(GroupInvitation) \
            .values(state=InvitationState.invalidated) \
            .where(GroupInvitation.state == InvitationState.valid)
    )
    await session.commit()

    if opt == 'Y':
        await group_invitation_handler.finish('Accepted group invitation')
    elif opt == 'N':
        await group_invitation_handler.finish('Rejected group invitation')
        
