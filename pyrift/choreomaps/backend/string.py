from __future__ import annotations

from typing import ClassVar, override

from pyrift.jobj import JList, JObj

from ..enum import NumberFormat
from .condition import Condition
from .value import Value

type String = str | BaseString

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


class JoinString(BaseString, type='Join'):
    '''
    Attributes:
        strings: Strings to concatenate
    '''
    
    strings: JList[String]


class FormatString(BaseString, type='Format'):
    '''
    Attributes:
        text: Format string including C#-style placeholders ("{0}", "{1}", etc.)
        args: String values to substitute for placeholders
    '''
    
    text: String
    args: JList[String]


class NumberString(BaseString, type='Number'):
    '''
    Attributes:
        value: Number to convert to string
        format: Number format to use
    ''' # TODO: update
    
    value: Value
    format: NumberFormat | None = None


class ArrayString(BaseString, type='Array'):
    '''
    Attributes:
        name: Name of the array to read from, or nil to read the local variable array.
    '''
    
    name: String | None


class SubString(BaseString, type='Sub'):
    '''
    Attributes:
        string: Text to extract substring from
        start: Character index to start at (0-indexed, if nil, from beginning)
        length: Maximum length of the resulting substring (if nil, whole string)
    '''
    
    string: String
    start: Value | None = None
    length: Value | None = None


class IfString(BaseString, type='If'):
    '''
    Attributes:
        condition: Condition to check.
        yes: String value if the condition is true.
        no: String value if the condition is false.
    '''
    
    condition: Condition
    yes: String
    no: String
