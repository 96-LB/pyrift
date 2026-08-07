
from dataclasses import dataclass

from .nodes import ArrayValue, ConstantValue


@dataclass
class Scope:
    vars: list[str]
    
    def get(self, name: str):
        return self.vars.index(name) if name in self.vars else None
    
    def set(self, name: str):
        self.vars.append(name)
    
    def list_vars(self):
        return tuple(self.vars)
    
    def get_locals(self):
        return tuple(ArrayValue(index=ConstantValue(i)) for i in range(len(self.vars)))
