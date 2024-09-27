from nonebot import require

require('nonebot_plugin_alconna')

from nonebot_plugin_orm import async_scoped_session

from sqlalchemy import select, delete, func
from aiohttp import ClientSession, MultipartWriter
from pathlib import Path
from typing import Any
from functional import seq
from puremagic import from_string
import re
from nonebot.log import logger
import asyncio
from typing import Literal

from .utils import download_file_to
from .db import Post, Bind, Shortcut

class Core:
    def __init__(self):
        self.root_dir = Path('./data/long/')
        self.url_base = 'https://longhub.top/api/'

    async def _get_shortcut(self, session: async_scoped_session, keyword: str, group_id: str) -> list[Shortcut]:
        res = await session.execute(
            select(Shortcut).where(Shortcut.group == group_id)
        )
        sh = res.scalars().all()

        result = []

        for i in sh:
            if i.type == 'match' and i.pattern in keyword:
                result.append(i)
            elif i.type == 'regex' and re.match(i.pattern, keyword):
                result.append(i)

        return result

    def dir_post(self, post: Post | str) -> Path:
        if isinstance(post, Post):
            return self.root_dir / 'post' / post.image
        else:
            return self.root_dir / 'post' / post
        
    async def rand(self, session: async_scoped_session) -> Post | None:
        res = await session.execute(
            select(Post).order_by(func.random()).limit(1)
        )

        return res.scalar_one_or_none()

    async def get(self, session: async_scoped_session, text: list[str], tags: list[str]) -> list[Post]:
        stmt = select(Post)

        for i in text:
            stmt = stmt.where(Post.text.like('%' + i + '%'))

        for i in tags:
            stmt = stmt.where(Post.tags.like("%'" + i + "'%"))

        res = await session.execute(stmt)

        return res.scalars().all()
    
    async def get_shortcut(self, session: async_scoped_session, keyword: str, group_id: str) -> list[Post]:
        shortcuts = await self._get_shortcut(session, keyword, group_id)
        stmt = select(Post).where(
            Post.id.in_(seq(shortcuts).map(lambda i: i.post_id))
        )

        res = await session.execute(stmt)
        return res.scalars().all()
    
    async def add_shortcut(self,
                           session: async_scoped_session,
                           type: Literal['match', 'regex'],
                           pattern: str,
                           group: str,
                           post_id: str):
        session.add(Shortcut(type=type, pattern=pattern, group=group, post_id=post_id))
    
    async def remove_shortcut_by_id(self, session: async_scoped_session, id: int):
        await session.execute(
            delete(Shortcut).where(Shortcut.id == id)
        )

    async def remove_shortcut_if_matches(self, session: async_scoped_session, group_id: str, keyword: str):
        shortcuts = await self._get_shortcut(session, keyword, group_id)

        if shortcuts:
            await session.execute(
                delete(Shortcut).where(Shortcut.id.in_(seq(shortcuts).map(lambda i: i.id)))
            )
    
    async def search(self, session: async_scoped_session, **kwargs):
        """
        `kwargs`:
            `id`
            `id_regex`
            `text_include`
            `text_exclude`
            `text_regex`
            `tag_include`
            `tag_exclude`
            `rating`
        """
        stmt = select(Post)

        for i in kwargs.get('id', []):
            stmt = stmt.where(Post.id.like('%' + i + '%'))
        for i in kwargs.get('id_regex', []):
            stmt = stmt.where(Post.id.regexp_match(i))
        for i in kwargs.get('text_include', []):
            stmt = stmt.where(Post.text.like('%' + i + '%'))
        for i in kwargs.get('text_exclude', []):
            stmt = stmt.where(Post.text.not_like('%' + i + '%'))
        for i in kwargs.get('text_regex', []):
            stmt = stmt.where(Post.text.regexp_match(i))
        for i in kwargs.get('tag_include', []):
            stmt = stmt.where(Post.tags.like('%' + i + '%'))
        for i in kwargs.get('tag_exclude', []):
            stmt = stmt.where(Post.tags.not_like('%' + i + '%'))
        for i in kwargs.get('rating', []):
            stmt = stmt.where(Post.rating == i)
        
        result = await session.execute(stmt)

        return result.scalars().all()

    async def bind(self, dbs: async_scoped_session, uid: str, key: str, reset: bool = False) -> dict[str, Any] | None:
        headers = {
            'X-Access-Key': key
        }
        result = None
        async with ClientSession(trust_env=True, headers=headers) as session:
            async with session.get(self.url_base + 'account') as response:
                if response.status == 200:
                    result: dict[str, Any] = await response.json()

            if result and reset:
                async with session.get(self.url_base + 'account/reset-key') as response:
                    result.update(await response.json())

        if result:
            _ = await dbs.execute(
                select(Bind).where(Bind.uid == uid)
            )
            binding = _.scalar_one_or_none()

            if binding is None:
                dbs.add(Bind(uid=uid, accessKey=result['accessKey']))
            else:
                binding.accessKey = result['accessKey']

        return result
    
    async def get_binding(self, dbs: async_scoped_session, uid: str) -> dict[str, Any] | None:
        res = await dbs.execute(
            select(Bind).where(Bind.uid == uid)
        )
        binding = res.scalar_one_or_none()

        if binding is None:
            return None
        
        headers = {
            'X-Access-Key': binding.accessKey
        }
        
        async with ClientSession(trust_env=True, headers=headers) as session:
            async with session.get(self.url_base + 'account') as response:
                if response.status == 200:
                    result = await response.json()
                else:
                    result = None

        return result
    
    async def unbind(self, dbs: async_scoped_session, uid: str):
        stmt = delete(Bind).where(Bind.uid == uid)

        await dbs.execute(stmt)
    
    async def upload(self,
                     uid: str,
                     dbs: async_scoped_session,
                     image: bytes,
                     text: str,
                     tags: list[str],
                     rating: str,
                     force: bool = False) -> dict[str, Any]:
        
        stmt = select(Bind).where(Bind.uid == uid)
        res = await dbs.execute(stmt)
        binding = res.scalar_one_or_none()

        if binding is None:
            raise Exception(f'User ID {uid} not bound to any account')
        
        key = binding.accessKey
        session = ClientSession(trust_env=True, headers={
            'X-Access-Key': key
        })
        result = None

        metadata = {
            'tags': tags,
            'text': text,
            'rating': rating
        }

        mime = from_string(image, mime=True)
        ext = from_string(image)

        with MultipartWriter('form-data') as mp:
            part = mp.append_json(metadata)
            part.set_content_disposition('form-data', name='metadata')

            part = mp.append(image, {'Content-Type': mime})
            part.set_content_disposition('form-data', name='image', filename='image' + ext)

            part = mp.append(str(int(force)))
            part.set_content_disposition('form-data', name='force')

            async with session.post(self.url_base + 'post', data=mp) as response:
                if response.status == 401:
                    raise Exception('401 Unauthorized. Try binding your account again')
                elif response.status == 419:
                    raise Exception('419 Payload too large')
                elif response.status == 409:
                    data = await response.json()
                    raise Exception('409 Conflict. Potential duplicate found: ' + data[0]['id'])
                elif not response.ok:
                    raise Exception(f'{response.status} {response.reason}')
                else:
                    result = await response.json()
        
        await session.close()

        return result

    async def sync(self, dbs: async_scoped_session):
        session = ClientSession(trust_env=True)

        async with session.get(self.url_base + 'post') as response:
            data = await response.json()
            total = data['count']

        logger.info('%d posts in total' % total)

        async with session.get(self.url_base + 'post?limit=' + str(total)) as response:
            data = (await response.json())['data']

        dl: list[tuple[str, str]] = []

        res = await dbs.execute(select(Post))
        local = dict(seq(res.scalars().all()).map(lambda x: (x.id, x)))

        for post in data:
            path = self.dir_post(post['image'])
            tags = ''.join(seq(post['tags']).map(lambda tag: f"'{tag['name']}'"))

            if not path.exists():
                dl.append((post['imageURL'], path))

            if not local.get(post['id']):
                dbs.add(Post(
                    id=post['id'],
                    image=post['image'],
                    text=post['text'],
                    tags=tags,
                    rating=post['rating']
                ))
            else:
                lp = local[post['id']]
                if lp.text != post['text'] or lp.tags != tags or lp.rating != post['rating']:
                    lp.text = post['text']
                    lp.tags = tags
                    lp.rating = post['rating']

        logger.info('%s posts to download' % len(dl))

        await asyncio.gather(*[ download_file_to(url, path, session) for url, path in dl ])

        await session.close()
