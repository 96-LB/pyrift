import inspect
from asyncio import sleep
from builtins import print as builtin_print
from enum import Enum, auto
from functools import wraps
from itertools import islice
from typing import Any, Concatenate, override

from pyrift.jobj import JList, JObj
from pyrift.util.typing import F

from .backend import (
    ArrayValue,
    BaseValue,
    Condition,
    GraphicCreateEvent,
    LogEvent,
    SetArrayEvent,
    SetVariableEvent,
    SpriteEvent,
    SpriteIDValue,
    SpriteStringEvent,
    String,
    Value,
    VariableValue,
)
from .context import BinaryOperator, MathValue, StreamContext
from .enum import GraphicType, SpriteAttribute, SpriteStringAttribute, VisualType
from .ir import AwaitExpression
from .vars import Tag

EXTERNALS: dict[str, ExternalValue] = {}

class ExternalArgType(Enum):
    VALUE = auto()
    CONDITION = auto()
    STRING = auto()

class ExternalArg(JObj):
    name: str
    type: ExternalArgType

class ExternalValue(BaseValue, type='$EXTERNAL'):
    func: ExternalFuncType
    args: JList[ExternalArg]
    is_async: bool
    
    @override
    def to_json_obj(self) -> None:
        raise NotImplementedError('External function cannot be converted to JSON object.')



type ExternalFuncType = F[Concatenate[StreamContext, ...], tuple[Value, Value | Condition | String]]

def register_external(func: ExternalFuncType, is_async: bool):
    def decorator[**P, T](stub: F[P, T]) -> F[P, T]:
        name = stub.__name__
        sig = inspect.signature(func)
        args: list[ExternalArg] = []
        for arg in islice(sig.parameters.values(), 1, None):
            arg_type = {
                Value: ExternalArgType.VALUE,
                Condition: ExternalArgType.CONDITION,
                String: ExternalArgType.STRING,
                None: None # for type-checking
            }.get(arg.annotation)
            if not arg_type:
                raise ValueError(f'Invalid type for argument "{arg}" of {func.__name__}: {arg.annotation}')
            args.append(ExternalArg(arg.name, arg_type))
        EXTERNALS[name] = ExternalValue(func, tuple(args), is_async)
        return stub
    return decorator

def external_func(func: ExternalFuncType):
    return register_external(func, is_async=False)

def external_coroutine(func: ExternalFuncType):
    @wraps(func)
    def wrapper(ctx: StreamContext, *args: Any, **kwargs: Any):
        parent = ctx.get_parent_instruction()
        if parent is not AwaitExpression:
            raise ValueError(f'External coroutine can only be used directly inside await expression, but parent is {parent.__name__}.')
        return func(ctx, *args, **kwargs)
    return register_external(wrapper, is_async=True)


def print_external(ctx: StreamContext, text: String):
    ctx.add_event(LogEvent(text))
    return Tag.STRING, text

@external_func(print_external)
def print[T](text: T) -> T:
    builtin_print(text)
    return text


def wait_external(ctx: StreamContext, seconds: Value):
    ctx.wait(seconds)
    return Tag.NONE, 0

@external_coroutine(wait_external)
async def wait(seconds: float):
    await sleep(seconds or 0)


def text_external(ctx: StreamContext):
    ref = VariableValue('$GRAPHIC')
    id = SpriteIDValue(VisualType.GRAPHIC, ref)
    # increment the heap counter
    ctx.add_event(SetVariableEvent('$GRAPHIC', MathValue(ref, 1, BinaryOperator.ADD)))
    # create the text graphic
    ctx.add_event(GraphicCreateEvent(ref, None, GraphicType.CANVAS_TEXT))
    ctx.add_event(SpriteEvent(id, SpriteAttribute.POSITION, None, 0, 0, 0, 0))
    # return a pointer to the text graphic
    tag_index, value_index = ctx.allocate_temp()
    ctx.add_event(SetArrayEvent(None, tag_index, Tag.NUMBER))
    ctx.add_event(SetArrayEvent(None, value_index, id))
    return ArrayValue(None, tag_index), ArrayValue(None, value_index)

class Text(int): ...

@external_func(text_external)
def text():
    return Text(0)

def set_text_external(ctx: StreamContext, id: Value, text: String):
    ctx.add_event(SpriteStringEvent(id, SpriteStringAttribute.TEXT, text))
    return Tag.NONE, 0

@external_func(set_text_external)
def set_text(id: Text, text: String):
    pass
