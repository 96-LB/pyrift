from functools import wraps
from inspect import Parameter, signature
from typing import TYPE_CHECKING, Concatenate
from typing_extensions import TypeForm

from ..jobj import JObj
from ..util.typing import F
from .ir import BaseExpression

if TYPE_CHECKING:
    from .compiler import ChoreomapCompiler, CompilerObject

type BuiltinF[**P] = F[Concatenate[ChoreomapCompiler, P], CompilerObject]
class Builtin(JObj):
    name: str
    func: F[Concatenate[ChoreomapCompiler, ...], CompilerObject]
    is_async: bool = False
    
    def call(self, compiler: ChoreomapCompiler, *args: BaseExpression) -> CompilerObject:
        return self.func(compiler, *args)

_stdlib: dict[str, Builtin] = {}
_converters: dict[TypeForm[CompilerObject], F[[ChoreomapCompiler, BaseExpression], CompilerObject]] = {}

def converter[T: CompilerObject](type: TypeForm[T]):
    def decorator(f: F[[ChoreomapCompiler, BaseExpression], T]) -> F[[ChoreomapCompiler, BaseExpression], T]:
        _converters[type] = f
        return f
    return decorator

def builtin(f: BuiltinF[...]) -> Builtin:
    name = f.__name__
    
    sig = signature(f)
    params = list(sig.parameters.values())[1:]
    
    for param in params:
        if param.kind is not Parameter.POSITIONAL_OR_KEYWORD:
            raise NotImplementedError(f'Argument {param.name} of {name} must be a positional or keyword argument.')
        
        if param.annotation not in _converters:
            raise NotImplementedError(f'Unsupported argument type {param.annotation} for builtin function {name}.')
    
    @wraps(f)
    def wrapper(compiler: ChoreomapCompiler, *args: BaseExpression) -> CompilerObject:
        expected_argc = len(params)
        argc = len(args)
        if argc != expected_argc:
            waswere = 'was' if argc == 1 else 'were'
            raise TypeError(f'{name} takes {expected_argc} positional arguments but {argc} {waswere} given.')
        
        builtin_args: list[CompilerObject] = []
        for arg, param in zip(args, params):
            converter = _converters[param.annotation]
            builtin_args.append(converter(compiler, arg))
        
        return f(compiler, *builtin_args)
    
    _stdlib[name] = Builtin(name, wrapper)
    return _stdlib[name]

def get_stdlib():
    from . import stdlib as _
    return _stdlib
