import inspect
from asyncio import sleep
from builtins import print as builtin_print
from collections.abc import Callable
from enum import Enum, auto
from typing import Concatenate, override

from pyrift.jobj import JList, JObj

from .backend import (
    BaseValue,
    Condition,
    IfEvent,
    LogEvent,
    String,
    Value,
    WaitEvent,
)
from .context import StreamContext
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


type ExternalFuncType = Callable[Concatenate[StreamContext, ...], tuple[Value, Value | Condition | String]]

def register_external(func: ExternalFuncType, is_async: bool):
    def decorator[**P, T](stub: Callable[P, T]) -> Callable[P, T]:
        name = stub.__name__
        spec = inspect.getfullargspec(func)
        args: list[ExternalArg] = []
        for arg in spec.args[1:]:
            type = {
                Value: ExternalArgType.VALUE,
                Condition: ExternalArgType.CONDITION,
                String: ExternalArgType.STRING,
                None: None # for type-checking
            }.get(spec.annotations.get(arg))
            if not type:
                raise ValueError(f'Invalid type for argument "{arg}" of {func.__name__}: {spec.annotations.get(arg)}')
            args.append(ExternalArg(arg, type))
        EXTERNALS[name] = ExternalValue(func, tuple(args), is_async)
        return stub
    return decorator

def external_func(func: ExternalFuncType):
    return register_external(func, is_async=False)

def external_coroutine(func: ExternalFuncType):
    return register_external(func, is_async=True)


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
async def wait(seconds: float | None = None):
    await sleep(seconds or 0)


def wait_until_external(ctx: StreamContext, condition: Condition):
    ctx.upgrade_timekeeping()
    
    # we don't wait directly on the condition because we need to re-evaluate side effects
    ctx.add_event(WaitEvent())
    ctx.add_event(IfEvent(condition, ctx.jump_up_stack(), None))
    
    return Tag.NONE, 0

@external_coroutine(wait_until_external)
async def wait_until(condition: bool):
    if not condition:
        # TODO: we probably don't want to softlock the compiler
        await sleep(0)
