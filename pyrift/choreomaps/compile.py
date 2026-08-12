import ast
import inspect
from types import ModuleType

from .compiler import ChoreomapCompiler
from .globals import GLOBAL
from .parser import ChoreomapParser


def compile(mod: ModuleType):
    '''Compiles a module to a choreomap by converting its AST to the choreomap DSL.'''
    
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    script = ChoreomapParser().visit_Module(tree)
    choreomap = ChoreomapCompiler().compile(script, GLOBAL)
    return choreomap
