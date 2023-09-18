import json
import os
from pathlib import Path

class Database(list):
    def __init__(self, root, name):
        self.root = Path(root).absolute()
        if not self.root.exists():
            os.makedirs(self.root)
            
        self.name = name
        
        try:
            with open(root / (name + '.json'), 'r', encoding='utf8') as f:
                super().__init__(json.loads(f.read()))
        except FileNotFoundError:
            with open(root / (name + '.json'), 'w') as f:
                f.write(json.dumps([]))
            super().__init__([])


    def reload(self):
        with open(self.root / (self.name + '.json'), 'r', encoding='utf8') as f:
            super().__init__(json.loads(f.read()))

    def save(self):
        with open(self.root / (self.name + '.json'), 'w', encoding='utf8') as f:
            f.write(json.dumps(self, ensure_ascii=False, indent=4))
    
    def file(self, file) -> Path:
        return self.root / self.name / file