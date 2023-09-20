import requests
import json

class LongHubAPI:
    def __init__(self, host):
        self.host = host
    
    def get_posts(self):
        res = requests.get(self.host + '/api/posts/')
        return json.loads(res.text)
    
    def get_templates(self):
        res = requests.get(self.host + '/api/templates/')
        return json.loads(res.text)



