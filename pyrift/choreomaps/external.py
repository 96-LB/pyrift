__all__ = ('log',)


from enum import Enum, auto
import inspect
from collections.abc import Callable
from typing import override

from pyrift.choreomaps.tag import Tag
from pyrift.choreomaps.ir.expression import BaseExpression
from pyrift.choreomaps.nodes.condition import Condition
from pyrift.choreomaps.nodes.event import BaseEvent, LogEvent
from pyrift.choreomaps.nodes.string import String
from pyrift.choreomaps.nodes.value import BaseValue, Value
from pyrift.jobj import JList, JObj

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

def external_func[**P, T](func: Callable[P, ExternalExpression]):
    def decorator(stub: Callable[P, T]) -> Callable[P, T]:
        name = stub.__name__
        spec = inspect.getfullargspec(stub)
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


def log_external(text: String):
    return ExternalExpression(
        events=(LogEvent(text),),
        tag=Tag.STRING,
        value=text
    )

@external_func(log_external)
def log(text: String) -> None:
    print(text)
