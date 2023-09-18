import re
import json
import shlex

class Item:
    def __init__(self, pattern='', type='true'):
        self.pattern = pattern
        self.type = type
        self.neg = False

    def parse(s: str):
        res = Item()
        pattern = s

        if pattern.startswith('!'):
            res.neg = True
            pattern = pattern[1:]

        if pattern == 't':
            return res
        elif (m := re.search(r'r\((.*)\)', pattern)) or (m := re.search(r'/(.*)/', pattern)):
            res.type = 'regex'
            res.pattern = m.group(1)
        elif m := re.search(r'e\((.*)\)', pattern):
            res.type = 'exact'
            res.pattern = m.group(1)
        elif m := re.search(r'c\((.*)\)', pattern):
            res.type = 'contains'
            res.pattern = m.group(1)
        else:
            res.type = 'contains'
            res.pattern = pattern

        return res

    def evaluate_str(self, s: str) -> bool:
        if self.type == 'true':
            return True ^ self.neg
        elif self.type == 'regex':
            return bool(re.match(self.pattern, s, re.IGNORECASE)) ^ self.neg
        elif self.type == 'exact':
            return (s == self.pattern) ^ self.neg
        elif self.type == 'contains':
            return (s.find(self.pattern) != -1) ^ self.neg
        else:
            raise NotImplementedError(self.type)

    def evaluate_list(self, a: list) -> bool:
        if len(a) == 0:
            return False

        for i in a:
            if self.evaluate_str(i):
                return True
            
        return False

    def evaluate(self, x: str | list) -> bool:
        if type(x) == list:
            return self.evaluate_list(x)
        elif type(x) == str:
            return self.evaluate_str(x)
        else:
            raise NotImplementedError(x)


class Selector():
    def __init__(self):
        self.text = []
        self.tags = []
        self.uid = []

    def parse(s: str):
        res = Selector()
        for i in shlex.split(s):
            i = i.strip()
            if not i:
                continue

            if i.startswith('#'):
                res.tags.append(Item.parse(i[1:]))
            elif i.startswith('='):
                res.uid.append(Item.parse(i[1:]))
            else:
                res.text.append(Item.parse(i))

        return res

    def match(self, a: list) -> list:
        res = []
        if max(len(self.text), len(self.tags), len(self.uid)) == 0:
            return a
        
        for i in a:
            suc = 1
            for x in self.text:
                if not x.evaluate(i['text']):
                    suc = 0
            for x in self.tags:
                if not x.evaluate(i['tags']):
                    suc = 0
            for x in self.uid:
                if not x.evaluate(i['uid']):
                    suc = 0
            if suc:
                res.append(i)

        return res


if __name__ == '__main__':
    test_data = []
    with open("../../../data/long/images.json", encoding='utf8') as f:
        test_data = json.loads(f.read())
    sel = Selector.parse("#原神 #原批")
    print(sel.match(test_data))
