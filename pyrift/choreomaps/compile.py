import ast

from .builtins import BuiltinsCompiler
from .parser import ChoreomapParser


def compile(filename: str):
    '''Compiles a file to a choreomap by converting its AST to the choreomap DSL.'''
    
    with open(filename, 'r') as file:
        source = file.read()
    tree = ast.parse(source)
    script = ChoreomapParser().visit_Module(tree)
    choreomap = BuiltinsCompiler().compile(script)
    return choreomap
