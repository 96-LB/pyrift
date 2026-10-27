from inspect import Parameter, signature
from typing import TYPE_CHECKING, Concatenate

from ..jobj import JObj
from ..util.typing import F
from .backend import Condition, String, TaggedValue
from .ir import BaseExpression

if TYPE_CHECKING:
    from .compiler import ChoreomapCompiler, CompilerObject

type BuiltinArg = TaggedValue | Condition | String
type BuiltinF[**P] = F[Concatenate[ChoreomapCompiler, P], CompilerObject]
class Builtin(JObj):
    name: str
    call_f: BuiltinF[...]
    is_async: bool = False
    
    def call(self, compiler: ChoreomapCompiler, *args: BaseExpression) -> CompilerObject:
        sig = signature(self.call_f)
        params = list(sig.parameters.values())[1:]
        
        expected_argc = len(params)
        argc = len(args)
        if argc != expected_argc:
            waswere = 'was' if argc == 1 else 'were'
            raise TypeError(f'{self.name} takes {expected_argc} positional arguments but {argc} {waswere} given.')
        
        builtin_args: list[BuiltinArg] = []
        for arg, param in zip(args, params):
            # TODO: should do this in a wrapper function for call_f at creation time
            if param.kind is not Parameter.POSITIONAL_OR_KEYWORD:
                raise TypeError(f'Argument {param.name} of {self.name} must be a positional or keyword argument.')
            argtype = param.annotation
            if argtype is TaggedValue:
                builtin_args.append(compiler.visit_value(arg))
            elif argtype is Condition:
                builtin_args.append(compiler.visit_condition(arg))
            elif argtype is String:
                builtin_args.append(compiler.visit_str(arg))
            else:
                raise NotImplementedError(f'Unsupported argument type {argtype} for builtin function {self.name}.')
        
        return self.call_f(compiler, *builtin_args)

_stdlib: dict[str, Builtin] = {}

def builtin(f: BuiltinF[...]) -> Builtin:
    name = f.__name__
    _stdlib[name] = Builtin(f.__name__, f)
    return _stdlib[name]

def get_stdlib():
    from . import stdlib as _
    return _stdlib

# class BuiltinsCompiler(ChoreomapCompiler):
#     @override
#     def call_builtin(self, obj: ExternalObject, *args: BaseExpression) -> CompilerObject:
#         def check_args(required_amount: int):
#             n = len(args)
#             if n != required_amount:
#                 waswere = 'was' if n == 1 else 'were'
#                 raise TypeError(f'{obj.name} takes {required_amount} positional arguments but {n} {waswere} given.')
        
#         match obj.name:
#             case 'print':
#                 check_args(1)
#                 text = self.visit_str(args[0])
#                 self.add_event(LogEvent(text))
#                 return text
            
#             case 'wait':
#                 check_args(1)
#                 _, time = self.visit_value(args[0]) # TODO: probably want some type-checking
#                 return ExternalCoroutine(obj.name, time)
            
#             case _:
#                 return super().call_builtin(obj)
    
#     @override
#     def await_builtin(self, obj: ExternalCoroutine) -> CompilerObject:
#         self.context.wait(obj.time)