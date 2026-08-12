from __future__ import annotations

from typing import ClassVar, override

from pyrift.jobj import JObj


class BaseString(JObj):
    '''
    Attributes:
        TYPE: String type
    '''
    
    TYPE: ClassVar[str]
    
    def __init_subclass__(cls, type: str):
        super().__init_subclass__()
        cls.TYPE = type
    
    @override
    def to_dict(self):
        return {**super().to_dict(), 'type': self.TYPE}


class ConstantString(BaseString, type='Constant'):
    '''
    Attributes:
        value: String value
    '''
    
    value: str
    
    @override
    def to_json_obj(self):
        return self.value
