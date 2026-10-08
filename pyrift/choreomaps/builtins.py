from typing import override

from .backend import LogEvent
from .compiler import ChoreomapCompiler, CompilerObject
from .external import ExternalCoroutine, ExternalObject
from .ir import BaseExpression


class BuiltinsCompiler(ChoreomapCompiler):
    @override
    def call_builtin(self, obj: ExternalObject, *args: BaseExpression) -> CompilerObject:
        def check_args(required_amount: int):
            n = len(args)
            if n != required_amount:
                waswere = 'was' if n == 1 else 'were'
                raise TypeError(f'{obj.name} takes {required_amount} positional arguments but {n} {waswere} given.')
        
        match obj.name:
            case 'print':
                check_args(1)
                text = self.visit_str(args[0])
                self.add_event(LogEvent(text))
                return text
            
            case 'wait':
                check_args(1)
                _, time = self.visit_value(args[0]) # TODO: probably want some type-checking
                return ExternalCoroutine(obj.name, time)
            
            case _:
                return super().call_builtin(obj)
    
    @override
    def await_builtin(self, obj: ExternalCoroutine) -> CompilerObject:
        self.context.wait(obj.time)
