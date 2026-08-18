import ast
from typing import override

from pyrift.choreomaps.enum import ComparisonMode
from pyrift.choreomaps.ir.instruction import DeclareVariablesInstruction
from pyrift.choreomaps.vars import VarType

from .ir import (
    AndExpression,
    BaseExpression,
    BaseInstruction,
    BinaryExpression,
    BooleanExpression,
    CallExpression,
    CompareExpression,
    FunctionExpression,
    IfExpression,
    IfInstruction,
    JoinExpression,
    NotExpression,
    NullExpression,
    NullInstruction,
    NumberExpression,
    OrExpression,
    ReturnInstruction,
    Script,
    SetVariableInstruction,
    StringExpression,
    UnaryExpression,
    VariableExpression,
)
from .backend import (
    BinaryOperator,
    UnaryOperator,
)


class ChoreomapParser(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
    
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
    
    def visit_operator(self, node: ast.operator) -> BinaryOperator:
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
        
        if type(node) not in MAPPING:
            raise NotImplementedError(f'Unsupported operator: {type(node).__name__}')
        return MAPPING[type(node)]
    
    @override
    def visit_Module(self, node: ast.Module):
        instructions = tuple(self.visit_stmt(stmt) for stmt in node.body)
        return Script(instructions)
    
    @override
    def visit_FunctionDef(self, node: ast.FunctionDef):
        name = node.name
        args = tuple(arg.arg for arg in node.args.args)
        instructions = tuple(self.visit_stmt(stmt) for stmt in node.body)
        return SetVariableInstruction(name, FunctionExpression(args, instructions))
    
    @override
    def visit_Return(self, node: ast.Return):
        expr = self.visit_expr(node.value) if node.value else NullExpression()
        return ReturnInstruction(expr)
    
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
        
        expr = self.visit_expr(node.value)
        match node.targets[0]:
            case ast.Name(var):
                return SetVariableInstruction(var, expr)
            case _:
                raise NotImplementedError(f'Unsupported assignment target: {type(node.targets[0]).__name__}')
    
    @override
    def visit_AugAssign(self, node: ast.AugAssign):
        expr = self.visit_expr(node.value)
        op = self.visit_operator(node.op)
        match node.target:
            case ast.Name(var):
                return SetVariableInstruction(var, BinaryExpression(VariableExpression(var), op, expr))
            case _:
                raise NotImplementedError(f'Unsupported assignment target: {type(node.target).__name__}')
    
    @override
    def visit_ImportFrom(self, node: ast.ImportFrom):
        print(f'Ignored import {', '.join(name.name for name in node.names)} from {node.module}')
        return NullInstruction()
    
    @override
    def visit_Global(self, node: ast.Global):
        return DeclareVariablesInstruction(tuple(node.names), VarType.GLOBAL)
    
    @override
    def visit_Nonlocal(self, node: ast.Nonlocal):
        return DeclareVariablesInstruction(tuple(node.names), VarType.NONLOCAL)
    
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
        operator = self.visit_operator(node.op)
        return BinaryExpression(left, operator, right)
    
    @override
    def visit_UnaryOp(self, node: ast.UnaryOp):
        expr = self.visit_expr(node.operand)
        match node.op:
            case ast.UAdd():
                return expr
            case ast.USub():
                return BinaryExpression(NumberExpression(0), BinaryOperator.SUBTRACT, expr)
            case ast.Invert():
                operator = UnaryOperator.NOT
            case ast.Not():
                return NotExpression(expr)
            case _:
                raise NotImplementedError(f'Unsupported unary operator: {type(node.op)}')
        return UnaryExpression(expr, operator)
    
    @override
    def visit_Lambda(self, node: ast.Lambda):
        expr = self.visit_expr(node.body)
        args = tuple(arg.arg for arg in node.args.args)
        return FunctionExpression(args, (ReturnInstruction(expr),))
    
    @override
    def visit_IfExp(self, node: ast.IfExp):
        condition = self.visit_expr(node.test)
        yes = self.visit_expr(node.body)
        no = self.visit_expr(node.orelse)
        return IfExpression(condition, yes, no)
    
    @override
    def visit_Compare(self, node: ast.Compare):
        MAPPING: dict[type[ast.cmpop], ComparisonMode] = {
            ast.Eq: ComparisonMode.EQUAL,
            ast.NotEq: ComparisonMode.NOT_EQUAL,
            ast.Lt: ComparisonMode.LESS,
            ast.LtE: ComparisonMode.LESS_EQUAL,
            ast.Gt: ComparisonMode.GREATER,
            ast.GtE: ComparisonMode.GREATER_EQUAL
        }
        
        first = self.visit_expr(node.left)
        operands = tuple(self.visit_expr(comp) for comp in node.comparators)
        operators: list[ComparisonMode] = []
        for op in node.ops:
            operator = MAPPING.get(type(op))
            if not operator:
                raise NotImplementedError(f'Unsupported comparison operator: {type(op)}')
            operators.append(operator)
        
        return CompareExpression(first, operands, tuple(operators))
    
    @override
    def visit_Call(self, node: ast.Call):
        func = self.visit_expr(node.func)
        args = tuple(self.visit_expr(arg) for arg in node.args)
        return CallExpression(func, args)
    
    @override
    def visit_FormattedValue(self, node: ast.FormattedValue):
        return self.visit_expr(node.value) # TODO: support actual formatting
    
    @override
    def visit_JoinedStr(self, node: ast.JoinedStr):
        strings = tuple(self.visit_expr(value) for value in node.values)
        return JoinExpression(strings)

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
