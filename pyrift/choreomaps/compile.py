import ast
import json

from .compiler import ChoreomapCompiler
from .parser import ChoreomapParser
from .assets import Assets

def compile(script_filename: str, assets_filename: str):
    '''Compiles a file to a choreomap by converting its AST to the choreomap DSL.'''
    
    with open(assets_filename, 'r') as file:
        assets = Assets.from_json(json.load(file))
    
    with open(script_filename, 'r') as file:
        source = file.read()
    tree = ast.parse(source)
    script = ChoreomapParser().visit_Module(tree)
    choreomap = ChoreomapCompiler(assets).compile(script)
    return choreomap
