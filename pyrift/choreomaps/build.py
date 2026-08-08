import ast
import inspect
from collections.abc import Sequence
from contextlib import contextmanager
from types import ModuleType
from typing import override

from . import globals
from .choreomap import Choreomap
from .nodes import (
    AndCondition,
    ArrayValue,
    BaseCondition,
    BaseEvent,
    BaseValue,
    BinaryOperator,
    CompareCondition,
    ComparisonMode,
    ConstantCondition,
    ConstantValue,
    IfEvent,
    IfValue,
    LogEvent,
    MathValue,
    NotCondition,
    OrCondition,
    SetArrayEvent,
    StartStreamEvent,
    Stream,
    UnaryOperator,
    UnaryValue,
)
from .scope import Scope


def build(mod: ModuleType):
    '''Reads a function as a choreomap stream by converting its AST to the choreomap DSL.'''
    
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    builder = ChoreomapBuilder()
    print(ast.dump(tree, indent=2))
    return builder.visit_Module(tree)

class ChoreomapBuilder(ast.NodeVisitor):
    def __init__(self):
        self.refs: int = 0
        self.func_map: dict[str, int] = {}
        self.streams: list[Stream] = []
        self.scopes: list[Scope] = []
        self.t: float = 0
    
    def make_id(self):
        self.refs += 1
        return self.refs
    
    def make_ref(self):
        return ConstantValue(self.make_id())
    
    def make_var(self, name: str):
        return f'{self.make_id()}_{name}'
    
    @contextmanager
    def new_scope(self, args: ast.arguments | None = None):
        self.scopes.append(Scope([arg.arg for arg in args.args] if args else []))
        yield
        self.scopes.pop()
    
    def visit_condition(self, node: ast.expr):
        value = self.visit(node)
        match value:
            case BaseCondition():
                return value
            case BaseValue():
                return CompareCondition(value, ConstantValue(0), ComparisonMode.NOT_EQUAL)
            case _:
                raise NotImplementedError(f'Unsupported condition: {type(value).__name__}')
    
    def visit_stream(self, nodes: Sequence[ast.AST]):
        events: list[BaseEvent] = []
        for node in nodes:
            child = self.visit(node)
            match child:
                case BaseEvent():
                    events.append(child)
                case BaseValue() | Stream() | None:
                    pass
                case _:
                    raise NotImplementedError(f'Unsupported statement: {type(child).__name__}')
        stream = Stream(
            id=len(self.streams) + 1,
            events=tuple(events),
            _vars=self.scopes[-1].list_vars()
        )
        print(f'Found stream {stream.id} in node {'::'.join(type(n).__name__ for n in nodes)}')
        self.streams.append(stream)
        
        return stream
    
    def start_stream(self, stream: Stream, immediate: bool, args: Sequence[BaseValue]):
        return StartStreamEvent(
            t=self.t,
            id=ConstantValue(stream.id),
            ref_id=self.make_ref(),
            immediate=ConstantCondition(immediate),
            locals=stream.pad_locals(args)
        )
    
    @override
    def generic_visit(self, node: ast.AST) -> None:
        raise NotImplementedError(f'Unsupported node: {type(node).__name__}')
    
    @override
    def visit_Module(self, node: ast.Module):
        with self.new_scope():
            stream = self.visit_stream(node.body)
        event = StartStreamEvent(
            t=self.t,
            id=ConstantValue(stream.id),
            ref_id=self.make_ref(),
            immediate=ConstantCondition(True),
            locals=stream.pad_locals(())
        )
        
        main = Stream(
            id=len(self.streams) + 1,
            events=(event,),
        )
        self.streams.append(main)
        # TODO: actually set the properties properly
        return Choreomap(
            streams=tuple(self.streams),
            input_rating_definitions=(),
            main_id=main.id
        )
    
    @override
    def visit_FunctionDef(self, node: ast.FunctionDef):
        with self.new_scope(node.args):
            stream = self.visit_stream(node.body)
        self.func_map[node.name] = stream.id - 1
        return stream
    
    @override
    def visit_If(self, node: ast.If):
        condition = self.visit_condition(node.test)
        
        body = self.visit_stream(node.body)
        orself = self.visit_stream(node.orelse)
        
        scope = self.scopes[-1]
        yes = self.start_stream(body, immediate=True, args=scope.get_locals())
        no = self.start_stream(orself, immediate=True, args=scope.get_locals()) if node.orelse else None
        
        return IfEvent(t=self.t, condition=condition, yes=yes, no=no)
    
    @override
    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) != 1:
            raise NotImplementedError('Only single-variable assignments are supported')
        
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise NotImplementedError('Only simple variable assignments are supported')
        
        value = self.visit(node.value)
        if not isinstance(value, BaseValue):
            raise NotImplementedError(f'Unsupported value in assignment: {type(value).__name__}')
        
        name = target.id
        scope = self.scopes[-1]
        index = scope.get(name)
        if index is None:
            scope.set(name)
            index = len(scope.vars) - 1
        
        event = SetArrayEvent(t=self.t, index=ConstantValue(index), value=value)
        return event
    
    @override
    def visit_ImportFrom(self, node: ast.ImportFrom):
        print(node.module)
    
    @override
    def visit_Expr(self, node: ast.Expr):
        return self.visit(node.value)
    
    @override
    def visit_BoolOp(self, node: ast.BoolOp):
        conditions = tuple(self.visit_condition(value) for value in node.values)
        
        match node.op:
            case ast.And():
                return AndCondition(conditions)
            case ast.Or():
                return OrCondition(conditions)
            case _:
                raise NotImplementedError(f'Unsupported boolean operator: {type(node.op)}')
    
    @override
    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        if not isinstance(left, BaseValue):
            raise NotImplementedError(f'Unsupported left operand in binary operation: {type(left).__name__}')
        
        right = self.visit(node.right)
        if not isinstance(right, BaseValue):
            raise NotImplementedError(f'Unsupported right operand in binary operation: {type(right).__name__}')
        
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
        
        return MathValue(left, right, op)
    
    @override
    def visit_UnaryOp(self, node: ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return NotCondition(self.visit_condition(node.operand))
        
        value = self.visit(node.operand)
        if not isinstance(value, BaseValue):
            raise NotImplementedError(f'Unsupported operand in unary operation: {type(value).__name__}')
        
        match node.op:
            case ast.UAdd():
                return value
            case ast.USub():
                return MathValue(ConstantValue(0), value, BinaryOperator.SUBTRACT)
            case ast.Invert():
                return UnaryValue(value, UnaryOperator.NOT)
            case _:
                raise NotImplementedError(f'Unsupported unary operator: {type(node.op)}')
    
    @override
    def visit_IfExp(self, node: ast.IfExp):
        condition = self.visit_condition(node.test)
        
        yes = self.visit(node.body)
        if not isinstance(yes, BaseValue):
            raise NotImplementedError(f'Unsupported value in if expression: {type(yes).__name__}')
        
        no = self.visit(node.orelse)
        if not isinstance(no, BaseValue):
            raise NotImplementedError(f'Unsupported value in if expression: {type(no).__name__}')
        
        return IfValue(condition=condition, yes=yes, no=no)
    
    @override
    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise NotImplementedError(f'Only simple function calls are supported: {type(node.func).__name__}')
        
        func_name = node.func.id
        if func_name in self.func_map:
            args: list[BaseValue] = []
            for arg in node.args:
                value = self.visit(arg)
                if not isinstance(value, BaseValue):
                    raise NotImplementedError(f'Unsupported argument in function call: {type(value).__name__}')
                args.append(value)
            
            return self.start_stream(
                self.streams[self.func_map[func_name]],
                immediate=False,
                args=tuple(args)
            )
        
        if func_name == globals.log.__name__:
            if not node.args:
                return None
            
            text = self.visit(node.args[0])
            if not isinstance(text, str):
                raise NotImplementedError(f'Unsupported text argument in log call: {type(text).__name__}')
            args: list[BaseValue] = []
            for arg in node.args[1:]:
                value = self.visit(arg)
                if not isinstance(value, BaseValue):
                    raise NotImplementedError(f'Unsupported argument in log call: {type(value).__name__}')
                args.append(value)
            return LogEvent(t=self.t, text=text, args=tuple(args))
        
        raise ValueError(f'Unknown function: {func_name}')
    
    @override
    def visit_Constant(self, node: ast.Constant):
        match node.value:
            case bool():
                return ConstantCondition(node.value)
            case int() | float():
                return ConstantValue(node.value)
            case str():
                return node.value
            case _:
                raise ValueError(f'Unsupported constant value: {node.value}')
    
    @override
    def visit_Name(self, node: ast.Name):
        name = node.id
        scope = self.scopes[-1]
        index = scope.get(name)
        if index is not None:
            return ArrayValue(index=ConstantValue(index))
