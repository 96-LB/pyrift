from collections.abc import Generator, Sequence
from contextlib import contextmanager

from pyrift.choreomaps.choreomap import Choreomap
from pyrift.choreomaps.enum import ComparisonMode
from pyrift.choreomaps.ir.expression import (
    AndExpression,
    BaseExpression,
    BinaryExpression,
    BooleanExpression,
    CallExpression,
    FunctionExpression,
    IfExpression,
    NumberExpression,
    OrExpression,
    StringExpression,
    UnaryExpression,
    VariableExpression,
)
from pyrift.choreomaps.ir.instruction import (
    BaseInstruction,
    IfInstruction,
    SetVariableInstruction,
)
from pyrift.choreomaps.ir.script import Script
from pyrift.choreomaps.nodes.condition import (
    AndCondition,
    BaseCondition,
    CompareCondition,
    ConstantCondition,
    OrCondition,
)
from pyrift.choreomaps.nodes.event import (
    BaseEvent,
    JumpEvent,
    SetArrayEvent,
    StartStreamEvent,
)
from pyrift.choreomaps.nodes.string import BaseString, ConstantString
from pyrift.choreomaps.nodes.value import (
    ArrayValue,
    BaseValue,
    IfValue,
    MathValue,
    UnaryValue,
    VariableValue,
)

from .nodes import ConstantValue
from .scope import Scope


class Compiler:
    def __init__(self):
        self.refs: int = 0
        self.func_map: dict[str, int] = {}
        self.streams: list[Scope] = []
        self.scopes: list[Scope] = []
    
    def make_id(self):
        self.refs += 1
        return self.refs
    
    def make_ref(self):
        return ConstantValue(self.make_id())
    
    @property
    def current_scope(self):
        return self.scopes[-1]
    
    def add_event(self, event: BaseEvent):
        self.current_scope.events.append(event)
    
    @contextmanager
    def new_scope(self, args: Sequence[str] | None = None) -> Generator[Scope, None, None]:
        scope = Scope(
            id=len(self.streams) + 1, # streams are 1-indexed by position
            args=list(args) if args else []
        )
        self.streams.append(scope)
        self.scopes.append(scope)
        yield scope
        self.scopes.pop()
    
    
    def compile(self, node: Script):
        self.visit_stream(node.instructions)
        
        # TODO: actually set the properties properly
        return Choreomap(
            streams=tuple(stream.to_stream() for stream in self.streams),
            input_rating_definitions=(),
            main_id=0
        )
    
    
    def visit_stream(self, nodes: Sequence[BaseInstruction]):
        with self.new_scope() as scope:
            for node in nodes:
                self.visit_inst(node)
            print(f'Found stream {scope.id} in node {'::'.join(type(n).__name__ for n in nodes)}')
        return scope

    
    def visit_inst(self, node: BaseInstruction) -> None:
        match node:
            case SetVariableInstruction(name, expr):
                scope = self.current_scope
                index = scope.get(name)
                if index is None:
                    scope.set(name)
                    index = len(scope.vars) - 1
                value = self.visit_value(expr)
                self.add_event(SetArrayEvent(t=0, index=ConstantValue(index), value=value))
            
            case IfInstruction(condition, yes, no):
                condition = self.visit_condition(condition)
                
                self.add_event(BaseEvent(0)) # placeholder jump
                
                yes_index = len(self.current_scope.events)
                for inst in yes:
                    self.visit_inst(inst)
                
                self.add_event(BaseEvent(0)) # placeholder jump
                
                no_index = len(self.current_scope.events)
                for inst in no:
                    self.visit_inst(inst)
                
                end_index = len(self.current_scope.events)
                self.current_scope.events[yes_index - 1] = JumpEvent(0, IfValue(condition, ConstantValue(yes_index), ConstantValue(no_index)))
                self.current_scope.events[no_index] = JumpEvent(0, ConstantValue(end_index))
            
            case _:
                raise NotImplementedError(f'Unsupported instruction: {type(node).__name__}')
    
    def visit_expr(self, node: BaseExpression) -> BaseValue | BaseCondition | BaseString:
        match node:
            case NumberExpression(value):
                return ConstantValue(value)
            
            case BooleanExpression(value):
                return ConstantCondition(value)
            
            case StringExpression(value):
                return ConstantString(value)
            
            case FunctionExpression(args, instructions):
                stream = self.visit_stream(instructions)
                return ConstantValue(stream.id) # TODO: closures...
            
            case VariableExpression(name):
                scope = self.current_scope
                index = scope.get(name)
                if index is not None:
                    return ArrayValue(index=ConstantValue(index))
                raise ValueError(f'Undefined variable: {name}')
            
            case AndExpression(conditions):
                conditions = tuple(self.visit_condition(condition) for condition in conditions)
                return AndCondition(conditions)
            
            case OrExpression(conditions):
                conditions = tuple(self.visit_condition(condition) for condition in conditions)
                return OrCondition(conditions)
            
            case BinaryExpression(left, operator, right):
                left = self.visit_value(left)
                right = self.visit_value(right)
                return MathValue(left, right, operator)
            
            case UnaryExpression(expr, operator):
                value = self.visit_value(expr)
                return UnaryValue(value, operator)
            
            case IfExpression(condition, yes, no):
                condition = self.visit_condition(condition)
                yes = self.visit_value(yes)
                no = self.visit_value(no)
                return IfValue(condition, yes, no)
            
            case CallExpression(func, args):
                func = self.visit_value(func)
                for i, arg in enumerate(args):
                    index = ConstantValue(i)
                    value = self.visit_value(arg)
                    self.add_event(SetArrayEvent(0, "$ARGS", index, value))
                self.add_event(StartStreamEvent(0, func, self.make_ref(), immediate=ConstantCondition(True)))
                
                index = ConstantValue(self.current_scope.temp())
                self.add_event(SetArrayEvent(0, index=index, value=VariableValue("$RETURN")))
                return ArrayValue(index=index)
            
            case _:
                raise NotImplementedError(f'Unsupported expression: {type(node).__name__}')
    
    def visit_value(self, node: BaseExpression):
        value = self.visit_expr(node)
        match value:
            case BaseCondition():
                return IfValue(value, ConstantValue(1), ConstantValue(0))
            case BaseValue():
                return value
            case BaseString():
                raise NotImplementedError(f'#TODO: implement strings')
    
    def visit_condition(self, node: BaseExpression):
        value = self.visit_expr(node)
        match value:
            case BaseCondition():
                return value
            case BaseValue():
                return CompareCondition(value, ConstantValue(0), ComparisonMode.NOT_EQUAL)
            case BaseString():
                raise NotImplementedError(f'#TODO: implement strings')
