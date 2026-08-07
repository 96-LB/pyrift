# from ast import If, NodeVisitor, parse
# import inspect
# from types import FunctionType
# from typing import override


# def stream(func: FunctionType):
#     '''Reads a function as a choreomap stream by converting its AST to the choreomap DSL.'''
    
#     source = inspect.getsource(func)
#     tree = parse(source)



# class StreamBuilder(NodeVisitor):
    
#     @override
#     def visit_If(self, node: If):
#         ...
