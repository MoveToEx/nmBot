import requests
import random
import string

class Cl1p:
    def __init__(self, token: str):
        assert token
        self.session = requests.Session()
        self.session.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.session.headers['cl1papitoken'] = token
    
    def create(self, text: str) -> str:
        key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        res = self.session.post('https://api.cl1p.net/' + key, data=text.encode())
        return 'https://cl1p.net/' + key
