__all__ = ('print',)


import inspect
from builtins import print as builtin_print
from collections.abc import Callable
from enum import Enum, auto
from typing import override

from pyrift.jobj import JList, JObj

from .ir import BaseExpression
from .nodes import BaseEvent, BaseValue, Condition, LogEvent, String, Value
from .vars import Tag

EXTERNALS: dict[str, ExternalValue] = {}

class ExternalArgType(Enum):
    VALUE = auto()
    CONDITION = auto()
    STRING = auto()

class ExternalArg(JObj):
    name: str
    type: ExternalArgType

class ExternalExpression(BaseExpression):
    events: JList[BaseEvent]
    tag: Value
    value: Value | Condition | String

class ExternalValue(BaseValue, type='$EXTERNAL'):
    func: Callable[..., ExternalExpression]
    args: JList[ExternalArg]
    
    @override
    def to_json_obj(self) -> None:
        raise NotImplementedError('External function cannot be converted to JSON object.')

def external_func(func: Callable[..., ExternalExpression]):
    def decorator[**P, T](stub: Callable[P, T]) -> Callable[P, T]:
        name = stub.__name__
        spec = inspect.getfullargspec(func)
        args: list[ExternalArg] = []
        for arg in spec.args:
            type = {
                Value: ExternalArgType.VALUE,
                Condition: ExternalArgType.CONDITION,
                String: ExternalArgType.STRING,
                None: None # for type-checking
            }.get(spec.annotations.get(arg))
            if not type:
                raise ValueError(f'Invalid type for argument "{arg}" of {name}: {spec.annotations.get(arg)}')
            args.append(ExternalArg(arg, type))
        EXTERNALS[name] = ExternalValue(func, tuple(args))
        return stub
    return decorator

def print_external(text: String):
    return ExternalExpression(
        events=(LogEvent(text),),
        tag=Tag.STRING,
        value=text
    )

@external_func(print_external)
def print[T](text: T) -> T:
    builtin_print(text)
    return text
