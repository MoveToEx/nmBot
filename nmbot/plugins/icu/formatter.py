from datetime import datetime
from shlex import split
from typing import Literal

import random

class Functions:
    def __init__(self):
        pass

    def date_delta(self, start: str, end: str, unit: Literal['d', 'min', 's', 'm', 'y'] = 'd'):
        assert unit in ['d', 'min', 's', 'm', 'y']
        
        if start.upper() == 'NOW':
            dstart = datetime.now()
        elif start.upper() == 'TODAY':
            dstart = datetime.today()
        else:
            dstart = datetime.strptime(start, '%Y/%m/%d')
        
        if end.upper() == 'NOW':
            dend = datetime.now()
        elif  end.upper() == 'TODAY':
            dend = datetime.today()
        else:
            dend = datetime.strptime(end, '%Y/%m/%d')

        delta = dend - dstart

        if unit == 'd':
            return delta.days
        elif unit == 'm':
            return delta.days // 30
        elif unit == 'y':
            return delta.days // 365
        elif unit == 'min':
            return int(delta.total_seconds() // 60)
        elif unit == 's':
            return int(delta.total_seconds())
        
        raise ValueError('Unknown unit: ' + unit)

class Formatter(dict):
    def __init__(self, object: str, subject: str):
        time = datetime.now()

        self.func = Functions()
        self.data = {
            '': object,
            'object': object,
            'subject': subject,
            'year': time.year,
            'month': time.month,
            'day': time.day,
            'random': random.random(),
            'randint': random.randint(1, 100)
        }

    def __getitem__(self, key):
        args = split(key)
        if len(args) == 1 and self.data.get(args[0]):
            return self.data.get(args[0])
        
        name = args[0]
        args.pop(0)

        for i, val in enumerate(args):
            if val.startswith('$') and val.removeprefix('$') in self.data:
                args[i] = self.data.get(val.removeprefix('$'))
        
        f = getattr(self.func, name)
        
        if not f:
            raise ValueError('Invalid callable name: ' + name)
        
        return f(*args)
