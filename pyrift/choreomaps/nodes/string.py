from __future__ import annotations

from typing import ClassVar, override

from pyrift.choreomaps.nodes.condition import BaseCondition
from pyrift.jobj import JList, JObj

from .value import BaseValue


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


class NumberString(BaseString, type='Number'):
    '''
    Attributes:
        value: numeric value
    ''' # TODO: update
    
    value: BaseValue


class JoinString(BaseString, type='Join'):
    '''
    Attributes:
        strings: fixed-size array of string expressions to join with no intermediate separator
    ''' # TODO: update
    
    strings: JList[BaseString]


class ArrayString(BaseString, type='Array'):
    """
    Attributes:
        name: Name of the array to read from, or nil to read the local variable array.
        index: Index to read from, or nil to read the array's length.
    """ # TODO: update, also this is overloaded
    
    name: BaseString


class IfString(BaseString, type='If'):
    """
    Attributes:
        condition: Condition to check.
        yes: Value if the condition is true.
        no: Value if the condition is false.
    """ # TODO: update
    
    condition: BaseCondition
    yes: BaseString
    no: BaseString
