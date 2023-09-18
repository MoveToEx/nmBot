import requests
import json
from base64 import b64encode
from cryptography.hazmat.primitives import *
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
import rsa


class Constant:
    iv = b'0102030405060708'
    presetKey = b'0CoJUm6Qyw8W8jud'
    eapiKey = b'e82ckenh8dichen8'
    linuxKey = b'rFgB&h#%2?^eDg:Q'
    base62 = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    publicKey = '-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDgtQn2JZ34ZC28NWYpAUd98iZ37BUrX/aKzmFbt7clFSs6sXqHauqKWqdtLkF2KexO40H1YTX8z2lSgBBOAxLsvaklV8k4cBFK9snQXE9/DDaFt6Rr7iVZMldczhC0JNgTz+SHXT6CBHuX3e9SdB1Ua44oncaTWz7OBGLbCiK45wIDAQAB\n-----END PUBLIC KEY-----'


class NCMAPI:
    def __init__(self):
        self.session = requests.Session()
        self.selected = 0

    def _aes(buffer, key, iv) -> bytes:
        if isinstance(buffer, str):
            buffer = buffer.encode()
        return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(buffer, AES.block_size))

    def _rsa(buffer, key) -> bytes:
        pubKey = RSA.import_key(key)
        keylength = rsa.common.byte_size(pubKey.n)
        padded = (keylength - len(buffer)) * b'\x00' + buffer
        payload = rsa.transform.bytes2int(padded)
        encrypted = rsa.core.encrypt_int(payload, pubKey.e, pubKey.n)
        return rsa.transform.int2bytes(encrypted, keylength).hex()

    def _call_weapi(self, path, obj):
        path = path.removeprefix('/')
        text = json.dumps(obj, ensure_ascii=False)
        secretKey = ''.join(map(lambda x: Constant.base62[x % 62], get_random_bytes(16))).encode()
        data = {
            "params": b64encode(NCMAPI._aes(
                b64encode(NCMAPI._aes(text, Constant.presetKey, Constant.iv)), secretKey, Constant.iv
            )).decode(),
            "encSecKey": NCMAPI._rsa(secretKey[::-1], Constant.publicKey)
        }
        res = self.session.post('https://music.163.com/weapi/' + path, data=data)
        return json.loads(res.content)

    def search(self, keyword, offset=0, type=1, limit=10) -> dict:
        res = self._call_weapi('cloudsearch/get/web', {
            "s": keyword,
            "offset": offset,
            "type": type,
            "limit": limit
        })

        if res['code'] != 200:
            raise Exception(res['code'])

        return res['result']

    def select(self, id: int) -> None:
        self.selected = id

    def detail(self, id: int | list[int]):
        if not id:
            id = self.selected

        if isinstance(id, int):
            id = [id]

        data = {
            'c': json.dumps([{"id": x} for x in id])
        }

        return self._call_weapi('v3/song/detail', data)
    
    def lyric(self, id: int):
        if not id:
            id = self.selected
        
        data = {
            'id': id,
            'cp': False,
            'tv': 0,
            'lv': 0,
            'rv': 0,
            'kv': 0,
            'yv': 0,
            'ytv': 0,
            'yrv': 0,
        }

        return self._call_weapi('song/lyric/v1', data)
