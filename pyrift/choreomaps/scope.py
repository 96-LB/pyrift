
from dataclasses import dataclass

from .nodes import ArrayValue, ConstantValue


@dataclass
class Scope:
    vars: list[str]
    
    def get(self, name: str):
        return self.vars.index(name) + 1 if name in self.vars else 0
    
    def set(self, name: str):
        self.vars.append(name)
    
    def list_vars(self):
        return tuple(self.vars)
    
    def get_locals(self):
        return tuple(ArrayValue(index=ConstantValue(i + 1)) for i in range(len(self.vars)))
