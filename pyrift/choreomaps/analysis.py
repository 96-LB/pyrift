from collections.abc import Generator, Iterable
from contextlib import contextmanager
from enum import Enum, auto

from pyrift.jobj import JList, JObj

from .ir import (
    BaseInstruction,
    BinaryExpression,
    BooleanExpression,
    CallExpression,
    CompareExpression,
    FormatExpression,
    FunctionExpression,
    IfExpression,
    IfInstruction,
    JoinExpression,
    LogInstruction,
    NotExpression,
    NullExpression,
    NullInstruction,
    NumberExpression,
    ReturnInstruction,
    Script,
    SetVariableInstruction,
    StringExpression,
    UnaryExpression,
    VariableExpression,
)


class VarType(Enum):
    LOCAL = auto()
    CAPTURED = auto()
    NONLOCAL = auto()
    GLOBAL = auto()
    EXTERNAL = auto()

class Analysis(JObj):
    scopes: JList[Scope]

class Scope(JObj):
    vars: JList[str]
    types: JList[VarType]
    argc: int
    
    def filter_args(self, *types: VarType):
        return ((i, var) for i, (var, var_type) in enumerate(zip(self.vars, self.types)) if var_type in types)


class ScopeAnalyzer:
    def __init__(self, parent: ScopeAnalyzer | None = None):
        self.parent: ScopeAnalyzer | None = parent
        self.vars: dict[str, VarType] = {}
        self.argc: int = 0
        self.type = VarType.LOCAL if self.parent else VarType.GLOBAL
    
    def get(self, name: str) -> VarType:
        if name not in self.vars:
            self.vars[name] = self.parent.capture(name) if self.parent else VarType.EXTERNAL
        return self.vars[name]
    
    def capture(self, name: str) -> VarType:
        if self.get(name) == VarType.LOCAL:
            self.vars[name] = VarType.CAPTURED
        return VarType.NONLOCAL if self.vars[name] == VarType.CAPTURED else self.vars[name]
    
    def set(self, name: str) -> VarType:
        if name not in self.vars:
            self.vars[name] = self.type
        elif self.vars[name] in (VarType.NONLOCAL, VarType.GLOBAL) and self.parent:
            raise ValueError('Setting nonlocal variables is not yet supported')
        return self.vars[name]
    
    def to_scope(self):
        return Scope(
            vars=tuple(var for var in self.vars),
            types=tuple(type for type in self.vars.values()),
            argc=self.argc
        )


class ChoreomapAnalyzer:
    def __init__(self):
        self.scopes: list[ScopeAnalyzer] = []
        self.scope: ScopeAnalyzer = ScopeAnalyzer()
    
    @contextmanager
    def new_scope(self, args: Iterable[str] = ()) -> Generator[ScopeAnalyzer]:
        id = len(self.scopes)
        parent = self.scope
        scope = ScopeAnalyzer(parent if id else None)
        for arg in args:
            scope.set(arg)
            scope.argc += 1
        
        self.scopes.append(scope)
        self.scope = scope
        yield scope
        self.scope = parent
    
    def analyze(self, script: Script):
        with self.new_scope():
            self.declare_vars(script.instructions)
            for inst in script.instructions:
                self.visit_inst(inst)
        return Analysis(tuple(scope.to_scope() for scope in self.scopes))
    
    def declare_vars(self, instructions: JList[BaseInstruction]):
        for inst in instructions:
            if isinstance(inst, SetVariableInstruction):
                self.scope.set(inst.name)
    
    def visit_inst(self, instruction: BaseInstruction):
        match instruction:
            case (
                NullInstruction()
                | NullExpression()
                | NumberExpression()
                | BooleanExpression()
                | StringExpression()
            ):
                pass
            
            case (
                ReturnInstruction(expr)
                | LogInstruction(expr)
                | NotExpression(expr)
                | UnaryExpression(expr)
            ):
                self.visit_inst(expr)
            
            case BinaryExpression(left, _, right):
                self.visit_inst(left)
                self.visit_inst(right)
            
            case IfExpression(condition, yes, no):
                self.visit_inst(condition)
                self.visit_inst(yes)
                self.visit_inst(no)
            
            case FormatExpression(_, args) | JoinExpression(args):
                for arg in args:
                    self.visit_inst(arg)
            
            case CallExpression(expr, args) | CompareExpression(expr, args):
                self.visit_inst(expr)
                for arg in args:
                    self.visit_inst(arg)
            
            case IfInstruction(condition, yes, no):
                self.visit_inst(condition)
                for inst in yes:
                    self.visit_inst(inst)
                for inst in no:
                    self.visit_inst(inst)
            
            case VariableExpression(name):
                self.scope.get(name)
            
            case SetVariableInstruction(name, expr):
                self.scope.set(name)
                self.visit_inst(expr)
            
            case FunctionExpression(args, body):
                with self.new_scope(args):
                    self.declare_vars(body)
                    for inst in body:
                        self.visit_inst(inst)
            
            case _:
                raise NotImplementedError(f'Unsupported instruction {type(instruction)}')
