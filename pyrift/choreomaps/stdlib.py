from .backend import LogEvent, String, TaggedValue
from .builtin import Builtin, builtin
from .compiler import ChoreomapCompiler
from .vars import Tag


@builtin
def print(compiler: ChoreomapCompiler, arg: String) -> None:
    compiler.add_event(LogEvent(arg))

@builtin
def wait(compiler: ChoreomapCompiler, seconds: TaggedValue) -> Builtin:
    def wait_seconds(compiler: ChoreomapCompiler) -> None:
        compiler.context.wait(seconds[1])
    
    with compiler.match(seconds[0]) as case:
        with case(Tag.NUMBER):
            pass
        with case():
            # TODO: compile-time error for typechecking
            compiler.raise_exception("wait() argument must be a number")
    
    return Builtin('wait', wait_seconds, is_async=True)
