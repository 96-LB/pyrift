import ast

from .compiler import ChoreomapCompiler
from .external import EXTERNALS
from .parser import ChoreomapParser


def compile(filename: str):
    '''Compiles a file to a choreomap by converting its AST to the choreomap DSL.'''
    
    with open(filename, 'r') as file:
        source = file.read()
    tree = ast.parse(source)
    script = ChoreomapParser().visit_Module(tree)
    choreomap = ChoreomapCompiler().compile(script, EXTERNALS)
    return choreomap
