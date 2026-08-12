import ast
import inspect
from types import ModuleType
from typing import override

from pyrift.choreomaps.ir.expression import (
    AndExpression,
    BaseExpression,
    BinaryExpression,
    BooleanExpression,
    CallExpression,
    IfExpression,
    NullExpression,
    NumberExpression,
    OrExpression,
    StringExpression,
    UnaryExpression,
    VariableExpression,
)
from pyrift.choreomaps.ir.instruction import (
    BaseInstruction,
    FunctionInstruction,
    IfInstruction,
    ReturnInstruction,
    SetVariableInstruction,
)

from .nodes import (
    BinaryOperator,
    UnaryOperator,
)


def build(mod: ModuleType):
    '''Reads a function as a choreomap stream by converting its AST to the choreomap DSL.'''
    
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    builder = ChoreomapParser()
    print(ast.dump(tree, indent=2))
    return builder.visit_Module(tree)

class ChoreomapParser(ast.NodeVisitor):
    @override
    def generic_visit(self, node: ast.AST) -> None:
        raise NotImplementedError(f'Unsupported node: {type(node).__name__}')
    
    def visit_expr(self, node: ast.expr) -> BaseExpression:
        expr = self.visit(node)
        assert isinstance(expr, BaseExpression)
        return expr
    
    def visit_stmt(self, node: ast.stmt) -> BaseInstruction:
        inst = self.visit(node)
        assert isinstance(inst, BaseInstruction)
        return inst
    
    @override
    def visit_Module(self, node: ast.Module):
        return tuple(self.visit_stmt(stmt) for stmt in node.body)
    
    @override
    def visit_FunctionDef(self, node: ast.FunctionDef):
        name = node.name
        args = tuple(arg.arg for arg in node.args.args)
        instructions = tuple(self.visit_stmt(stmt) for stmt in node.body)
        return FunctionInstruction(name, args, instructions)
        
    @override
    def visit_Return(self, node: ast.Return):
        value = self.visit_expr(node.value) if node.value else NullExpression()
        return ReturnInstruction(value)
    
    @override
    def visit_If(self, node: ast.If):
        condition = self.visit_expr(node.test)
        yes = tuple(self.visit_stmt(stmt) for stmt in node.body)
        no = tuple(self.visit_stmt(stmt) for stmt in node.orelse)
        
        return IfInstruction(condition, yes, no)
    
    @override
    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) != 1:
            raise NotImplementedError('Only single-variable assignments are supported')
        
        var = self.visit_expr(node.targets[0])
        value = self.visit_expr(node.value)
        return SetVariableInstruction(var, value)
    
    @override
    def visit_ImportFrom(self, node: ast.ImportFrom):
        print(f'Ignored import {', '.join(name.name for name in node.names)} from {node.module}')
    
    @override
    def visit_Expr(self, node: ast.Expr):
        return self.visit_expr(node.value)
    
    @override
    def visit_BoolOp(self, node: ast.BoolOp):
        conditions = tuple(self.visit_expr(value) for value in node.values)
        
        match node.op:
            case ast.And():
                return AndExpression(conditions)
            case ast.Or():
                return OrExpression(conditions)
            case _:
                raise NotImplementedError(f'Unsupported boolean operator: {type(node.op)}')
    
    @override
    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit_expr(node.left)
        right = self.visit_expr(node.right)
        
        MAPPING: dict[type[ast.operator], BinaryOperator] = {
            ast.Add: BinaryOperator.ADD,
            ast.Sub: BinaryOperator.SUBTRACT,
            ast.Mult: BinaryOperator.MULTIPLY,
            ast.Div: BinaryOperator.DIVIDE,
            ast.Mod: BinaryOperator.MOD,
            ast.Pow: BinaryOperator.POWER,
            ast.BitOr: BinaryOperator.OR,
            ast.BitAnd: BinaryOperator.AND,
            ast.BitXor: BinaryOperator.XOR,
            ast.LShift: BinaryOperator.L_SHIFT,
            ast.RShift: BinaryOperator.R_SHIFT
        }
        
        op = MAPPING.get(type(node.op))
        if not op:
            raise NotImplementedError(f'Unsupported binary operator: {type(node.op)}')
        
        return BinaryExpression(left, op, right)
    
    @override
    def visit_UnaryOp(self, node: ast.UnaryOp):
        expr = self.visit_expr(node)
        match node.op:
            case ast.UAdd():
                return expr
            case ast.USub():
                return BinaryExpression(NumberExpression(0), BinaryOperator.SUBTRACT, expr)
            case ast.Invert():
                operator = UnaryOperator.NOT
            case _:
                raise NotImplementedError(f'Unsupported unary operator: {type(node.op)}')
        return UnaryExpression(expr, operator)
    
    @override
    def visit_IfExp(self, node: ast.IfExp):
        condition = self.visit_expr(node.test)
        yes = self.visit_expr(node.body)
        no = self.visit_expr(node.orelse)
        return IfExpression(condition, yes, no)
    
    @override
    def visit_Call(self, node: ast.Call):
        func = self.visit_expr(node.func)
        args = tuple(self.visit_expr(arg) for arg in node.args)
        return CallExpression(func, args)
    
    @override
    def visit_Constant(self, node: ast.Constant):
        match node.value:
            case None:
                return NullExpression()
            case bool():
                return BooleanExpression(node.value)
            case int() | float():
                return NumberExpression(node.value)
            case str():
                return StringExpression(node.value)
            case _:
                raise ValueError(f'Unsupported constant value: {node.value}')
    
    @override
    def visit_Name(self, node: ast.Name):
        return VariableExpression(node.id)
