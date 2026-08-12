__all__ = ('log',)


from collections.abc import Callable
import inspect

from pyrift.choreomaps.ir.expression import FunctionExpression, VariableExpression
from pyrift.choreomaps.ir.instruction import BaseInstruction, LogInstruction, SetVariableInstruction


GLOBAL: list[BaseInstruction] = []

def global_func(*body: BaseInstruction):
    def decorator[**P, T](func: Callable[P, T]) -> Callable[P, T]:
        name = func.__name__
        spec = inspect.getfullargspec(func)
        args = tuple(spec.args)
        GLOBAL.append(SetVariableInstruction(name, FunctionExpression(args, body)))
        return func
    return decorator


@global_func(LogInstruction(VariableExpression('text')))
def log(text: str) -> None:
    print(text)
