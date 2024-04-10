import json
import random
from pathlib import Path
from nonebot import logger
import asyncio
import sqlite3
import time
import re
import aiohttp
import puremagic
import mimetypes
from functional import seq
from typing import Literal

type ShortcutType = Literal['match', 'regex']

class Selector:
    type: str
    op: str | None
    value: str
    def __init__(self, type: str, op: str | None, value: str | None = None) -> None:
        self.type = type
        self.op = op
        self.value = value

class Post:
    id: str
    image: str
    text: str
    tags: list[str]
    aggr: float
    def __init__(self, rootdir: Path, **kwargs):
        self.id = kwargs.get('id', '')
        self.image = rootdir / kwargs.get('image', '')
        self.text = kwargs.get('text', '')
        if kwargs.get('tags'):
            self.tags = kwargs.get('tags').split(',')
        else:
            self.tags = []
        self.aggr = kwargs.get('aggr', '')

class Shortcut:
    id: int
    type: ShortcutType
    pattern: str
    postId: str
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '')
        self.type = kwargs.get('type', '')
        self.pattern = kwargs.get('pattern', '')
        self.postId = kwargs.get('postId', '')

type Query = list[Selector]

def parse_query(args: list[str]) -> Query:
    res: Query = []
    for s in args:
        if s.startswith(('#', '!#')):
            res.append(Selector('tag', 'include' if s.startswith('#') else 'exclude', s.removeprefix('!').removeprefix('#')))
        elif s.startswith(('>', '<', '=', '!=')):
            arg = re.match(r'^([^0-9\.]+)([0-9\.]+)$', s)
            if arg is None or arg.group(1) not in ['=', '!=', '<', '<=', '>', '>=']:
                continue
            res.append(Selector('aggr', arg.group(1), float(arg.group(2))))
        elif s.startswith('@'):
            res.append(Selector('id', None, s.removeprefix('@').replace('*', '%')))
        elif s.startswith(':'):
            if s == ':r':
                res.append(Selector('index', 'random'))
            elif s == ':l':
                res.append(Selector('index', 'last'))
            elif s.removeprefix(':').isdigit():
                res.append(Selector('index', 'number', int(s[1:])))
        else:
            res.append(Selector('text', 'exclude' if s.startswith('!') else 'include', s))
    return res


class Database:
    def __init__(self, host = 'https://longhub.top', rootdir = './data/long'):
        self.upstream = host
        self.rootdir = Path(rootdir).absolute()
        self.db = sqlite3.connect(self.rootdir / 'db.sqlite')
        self.db.row_factory = sqlite3.Row
        cursor = self.db.cursor()

        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS post (
                id TEXT PRIMARY KEY,
                text TEXT,
                aggr REAL,
                tags TEXT,
                image TEXT
            );""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shortcut (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                pattern TEXT,
                postId TEXT NOT NULL,
                FOREIGN KEY(postId) REFERENCES post(id) ON UPDATE CASCADE
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT,
                x INTEGER,
                y INTEGER,
                width INTEGER,
                height INTEGER,
                image TEXT
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bind (
                qqid TEXT PRIMARY KEY,
                accessKey TEXT
            );""")
        
        self.db.commit()

        if not self.rootdir.exists():
            self.rootdir.mkdir()

        with self.rootdir.joinpath('post') as p:
            if not p.exists():
                p.mkdir()


    async def _download(self, session: aiohttp.ClientSession, dest: Path, url: str):
        while True:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.info('Failed when downloading ' + url + ', retrying')
                    continue

                with open(dest, 'wb') as f:
                    f.write(await response.content.read())
                logger.info('Downloaded ' + url)
                break

    def _get_auth_session(self, qqid: str | None = None, key: str | None = None):
        if not qqid and not key:
            return None
        
        if qqid:
            cur = self.db.cursor()
            cur.execute('SELECT accessKey FROM bind WHERE qqid = ?', (qqid, ))
            res = cur.fetchone()

            if res is None:
                return None

            key = res[0]

        return aiohttp.ClientSession(trust_env=True, headers={
            'X-Access-Key': key
        })
    
    async def ping(self) -> tuple[bool, str]:
        session = aiohttp.ClientSession(trust_env=True)
        result = ()
        start = time.time()

        try:
            async with session.get(self.upstream) as response:
                if not response.ok:
                    result = (False, 'Status code ' + str(response.status))
                duration = time.time() - start
                result = (True, str(int(duration * 1000)) + 'ms')
                response.close()
        except aiohttp.ClientError as e:
            result = (False, str(e))

        await session.close()
        return result
        
    def size(self) -> int:
        cur = self.db.cursor()
        cur.execute('SELECT COUNT(*) FROM post;')
        size: tuple[int] = cur.fetchone()
        return size[0]
    
    async def validate_key(self, key: str) -> str | None:
        session = aiohttp.ClientSession(headers={
            'X-Access-Key': key
        })
        result = None

        async with session.get(self.upstream + '/api/account') as response:
            if response.ok:
                data = await response.json()
                result = data['name']
        
        await session.close()
        return result
    
    def bind(self, qqid: str, key: str):
        cur = self.db.cursor()
        cur.execute("""
                    INSERT INTO bind(qqid, accessKey) VALUES (?, ?)
                    ON CONFLICT DO UPDATE SET accessKey = ?""",
                    (qqid, key, key))
        self.db.commit()

    def unbind(self, qqid: str):
        cur = self.db.cursor()
        cur.execute('DELETE FROM bind WHERE qqid = ?', (qqid, ))
        self.db.commit()

    async def account_info(self, qqid: str):
        session = self._get_auth_session(qqid)

        if session is None:
            return None

        async with session.get(self.upstream + '/api/account') as response:
            if not response.ok:
                return None
            
            data = await response.json()
        
        await session.close()

        return data

    async def reset_key(self, key: str) -> tuple[bool, str]:
        session = self._get_auth_session(key=key)
        result: tuple[bool, str] = ()
        async with session.get(self.upstream + '/api/account/reset-key') as response:
            if response.ok:
                content = await response.json()
                result = (True, content['accessKey'])
            else:
                result = (False, str(response.status))
        await session.close()
        return result

    async def sync(self):
        added = 0
        removed = 0
        modified = 0

        session = aiohttp.ClientSession(trust_env=True)

        async with session.get(self.upstream + '/api/post') as response:
            data = await response.json()
            count: int = data['count']
            logger.info('Total posts: ' + str(count))

        async with session.get(self.upstream + '/api/post?limit=' + str(count)) as response:
            data = await response.json()
            posts: list = data['data']

        uncached_images: list[tuple[Path, str]] = []

        cur = self.db.cursor()

        cur.execute('SELECT id, text, aggr, tags FROM post;')

        local_posts = dict(seq(cur.fetchall()).map(lambda x: (x['id'], {
            'text': x['text'],
            'aggr': x['aggr'],
            'tags': x['tags']
        })))

        for post in posts:
            dirname = self.rootdir / 'post'
            tags = ''.join([ '\'' + tag['name'] + '\'' for tag in post['tags'] ])

            if not dirname.joinpath(post['image']).exists():
                uncached_images.append((dirname / post['image'], post['imageURL']))

            local_post = local_posts.get(post['id'], None)

            if not local_post:
                added = added + 1
                cur.execute(
                    'INSERT INTO post(id, text, aggr, tags, image) VALUES (?,?,?,?,?);',
                    (post['id'], post['text'], post['aggr'], tags, post['image'])
                )
            else:
                
                if local_post['text'] != post['text'] or local_post['tags'] != tags or local_post['aggr'] != local_post['aggr']:
                    modified = modified + 1
                    cur.execute(
                        'UPDATE post SET text = ?, aggr = ?, tags = ? WHERE id = ?;',
                        (post['text'], post['aggr'], tags, post['id'])
                    )

                local_posts.pop(post['id'])

        if len(local_posts):
            for post in local_posts:
                removed = removed + 1
                cur.execute('DELETE FROM post WHERE id = ?', (post,))
        
        self.db.commit()

        await asyncio.gather(
            *[ self._download(session, path, url) for [path, url] in uncached_images ]
        )
        await session.close()

        return (added, removed, modified)
    
    def new_shortcut(self, type: ShortcutType, pattern: str, post_id: str) -> tuple[bool, str | None]:
        cur = self.db.cursor()
        cur.execute('SELECT * FROM post WHERE id = ?;', (post_id, ))
        if cur.fetchone() is None:
            return [False, 'Post ' + post_id + ' does not exist. Try syncing with upstream.']
        cur.execute('INSERT INTO shortcut(type, pattern, postId) VALUES (?, ?, ?);', (type, pattern, post_id))
        self.db.commit()
        return [True, None]

    def get(self, query: Query) -> list[Post]:
        sql = 'SELECT * FROM post'
        dirname = self.rootdir / 'post'
        where: list[str] = []
        args: list[str] = []

        idx = seq(query).filter(lambda x: x.type == 'index').to_list()
        if len(idx) > 1:
            return []

        if query:
            sql += ' WHERE '

            for sel in query:
                if sel.type == 'text':
                    if sel.op == 'include':
                        where.append('text LIKE ?')
                    elif sel.op == 'exclude':
                        where.append('text NOT LIKE ?')
                    args.append('%' + sel.value + '%')
                elif sel.type == 'aggr':
                    if sel.op == '!=':
                        where.append('aggr <> ?')
                    else:
                        where.append('aggr %s ?' % sel.op)
                    args.append(sel.value)
                elif sel.type == 'tag':
                    if sel.op == 'include':
                        where.append('tags LIKE ?')
                    elif sel.op == 'exclude':
                        where.append('tags NOT LIKE ?')
                    args.append('%\'' + sel.value + '\'%')
                elif sel.type == 'id':
                    where.append('id LIKE ?')
                    args.append('%' + sel.value.replace('*', '%') + '%')

            sql += ' AND '.join(where) + ';'
        
        logger.debug(sql)

        cursor = self.db.cursor()
        cursor.execute(sql, args)

        result: list[Post] = seq(cursor.fetchall()).map(lambda x: Post(dirname, **dict(x))).to_list()

        if idx:
            idx = idx[0]
            if idx.op == 'random':
                return [ random.choice(result) ]
            elif idx.op == 'last':
                return [ result[-1] ]
            elif idx.op == 'number':
                if idx.value < 0 or idx.value >= len(result):
                    return []
                else:
                    return [ result[idx.value] ]
        
        return result
    
    def get_shortcut(self, msg: str) -> list[Post]:
        dirname = self.rootdir / 'post'
        cur = self.db.cursor()
        cur.execute('SELECT * FROM shortcut;')
        
        a: list[Shortcut] = seq(cur.fetchall()).map(lambda x: Shortcut(**dict(x)))

        resultId: list[str] = []
        result: list[Post] = []

        for shortcut in a:
            if shortcut.type == 'match' and shortcut.pattern in msg:
                resultId.append(shortcut.postId)
            elif shortcut.type == 'regex' and re.search(shortcut.pattern, msg):
                resultId.append(shortcut.postId)

        if len(resultId) == 0:
            return []

        cur.execute('SELECT * FROM post WHERE id IN (' + ','.join(['?'] * len(resultId)) + ')', resultId)

        result = seq(cur.fetchall()).map(lambda x: Post(dirname, **dict(x))).to_list()

        return result
    
    def list_shortcut(self) -> list[Shortcut]:
        cur = self.db.cursor()
        cur.execute('SELECT * FROM shortcut;')
        return seq(cur.fetchall()).map(lambda x: Shortcut(**dict(x))).to_list()
    
    def remove_shortcut(self, id: int) -> tuple[bool, str | None]:
        cur = self.db.cursor()

        cur.execute('SELECT * FROM shortcut WHERE id = ?', (id, ))
        _ = cur.fetchone()

        if _ is None:
            return (False, 'Shortcut #' + str(id) + ' does not exist')
        
        cur.execute('DELETE FROM shortcut WHERE id = ?', (id, ))
        self.db.commit()

        return (True, None)
    
    async def similar(self, image: bytes):
        session = aiohttp.ClientSession(trust_env=True)

        mime = puremagic.from_string(image)
        ext = mimetypes.guess_extension(mime)

        with aiohttp.MultipartWriter('form-data') as mp:
            mp.append(image, { 'Content-Type': mime }).set_content_disposition('form-data', name='image', filename='image' + ext)
            async with session.post(self.upstream + '/api/post/similar', data=mp) as response:
                if response.status == 419:
                    result = (False, 'Payload too large')
                else:
                    result = (response.ok, await response.json())
                response.close()

        await session.close()

        return result
    
    def purge(self) -> tuple[bool, int]:
        cursor = self.db.cursor()
        cursor.execute('SELECT COUNT(*) FROM post')
        count = cursor.fetchone()
        cursor.execute('DELETE FROM post')
        self.db.commit()
        size = 0

        for file in self.rootdir.joinpath('post').iterdir():
            size += file.stat().st_size
            file.unlink()

        return (count, size)

    
    async def upload(self, image: str | bytes, args: list[str], uid: str) -> tuple[bool, str | dict]:
        session = self._get_auth_session(qqid=uid)

        if session == None:
            return (False, 'LONG Hub account not bound')
        
        force = seq(args).map(lambda x: x == '!').any()

        aggr = seq(args).filter(lambda x: x.startswith('=')).map(lambda x: x.removeprefix('='))
        if aggr:
            aggr = float(aggr.last())
        else:
            aggr = 0

        result = ()
    
        metadata = {
            'tags': seq(args).filter(lambda x: x.startswith('#')).map(lambda x: x.removeprefix('#')).to_list(),
            'text': ''.join(seq(args).filter(lambda x: not (x.startswith(('#', '!', '='))))),
            'aggr': aggr
        }

        if isinstance(image, str):
            async with session.get(image) as response:
                image = await response.read()
        
        mime = puremagic.from_string(image, mime=True)
        ext = mimetypes.guess_extension(mime)
        
        try:
            with aiohttp.MultipartWriter('form-data') as mp:
                mp.append(json.dumps(metadata, ensure_ascii=False), { 'Content-Type': 'application/json' }).set_content_disposition('form-data', name='metadata')
                mp.append(image, { 'Content-Type': mime }).set_content_disposition('form-data', name='image', filename='image' + ext)
                mp.append(str(int(force))).set_content_disposition('form-data', name='force')

                async with session.post(self.upstream + '/api/post', data=mp) as response:
                    if response.status == 419:
                        result = (False, 'Payload too large')
                    elif response.status == 409:
                        data = await response.json()
                        if len(data) > 12:
                            data = data[:12]
                        dup = ','.join(seq(data).map(lambda x: x['id']))
                        result = (response.ok, 'Potential duplicates found: ' + dup)
                    else:
                        result = (response.ok, await response.json())
        except aiohttp.ClientError as e:
            return (False, str(e))
                
        await session.close()

        return result