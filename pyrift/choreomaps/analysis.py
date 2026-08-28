from collections.abc import Generator, Iterable
from contextlib import contextmanager

from pyrift.jobj import JList, JObj

from .ir import (
    AwaitExpression,
    BaseInstruction,
    BinaryExpression,
    BooleanExpression,
    CallExpression,
    CompareExpression,
    DeclareVariablesInstruction,
    FormatExpression,
    FunctionExpression,
    IfExpression,
    IfInstruction,
    JoinExpression,
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
from .vars import VarType


class Analysis(JObj):
    scopes: JList[Scope]

class Scope(JObj):
    vars: JList[str]
    types: JList[VarType]
    argc: int
    
    def filter_args(self, *types: VarType):
        return ((i, var) for i, (var, var_type) in enumerate(zip(self.vars, self.types)) if var_type in types)
    
    @classmethod
    def empty(cls):
        return cls((), (), 0)


class ScopeAnalyzer:
    def __init__(self, parent: ScopeAnalyzer | None = None):
        self.parent: ScopeAnalyzer | None = parent
        self.vars: dict[str, VarType] = {}
        self.argc: int = 0
        self.type = VarType.LOCAL if self.parent else VarType.GLOBAL
    
    def declare(self, name: str, type: VarType | None = None):
        if name in self.vars:
            if type:
                raise ValueError(f'Variable {name} cannot be declared as type {type}; it is already declared as type {self.vars[name]}.')
            return
        
        self.vars[name] = type or self.type
        
        # if we declared a variable nonlocal, make sure we can actually capture it
        if type is VarType.NONLOCAL and (not self.parent or self.parent.capture(name) is not VarType.NONLOCAL):
            raise ValueError(f'Variable {name} was declared nonlocal but cannot be found in enclosing scope.')
    
    def get(self, name: str) -> VarType:
        if name not in self.vars:
            self.vars[name] = self.parent.capture(name) if self.parent else VarType.EXTERNAL
        return self.vars[name]
    
    def capture(self, name: str) -> VarType:
        if self.get(name) is VarType.LOCAL:
            self.vars[name] = VarType.CAPTURED
        return VarType.NONLOCAL if self.vars[name] is VarType.CAPTURED else self.vars[name]
    
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
    
    def analyze(self, script: Script):
        self.visit_scope((), script.instructions)
        return Analysis(tuple(scope.to_scope() for scope in self.scopes))
    
    @contextmanager
    def new_scope(self, args: Iterable[str] = ()) -> Generator[ScopeAnalyzer]:
        id = len(self.scopes)
        parent = self.scope
        scope = ScopeAnalyzer(parent if id else None)
        for arg in args:
            scope.declare(arg)
            scope.argc += 1
        
        self.scopes.append(scope)
        self.scope = scope
        yield scope
        self.scope = parent
    
    def declare_vars(self, instructions: JList[BaseInstruction]):
        for inst in instructions:
            match inst:
                case SetVariableInstruction(name):
                    self.scope.declare(name)
                case DeclareVariablesInstruction(names, type):
                    for name in names:
                        self.scope.declare(name, type)
                case _:
                    pass
    
    def visit_scope(self, args: Iterable[str], instructions: JList[BaseInstruction]):
        with self.new_scope(args):
            self.declare_vars(instructions)
            for inst in instructions:
                self.visit_inst(inst)
    
    def visit_inst(self, instruction: BaseInstruction):
        match instruction:
            case (
                NullInstruction()
                | DeclareVariablesInstruction()
                | NullExpression()
                | NumberExpression()
                | BooleanExpression()
                | StringExpression()
            ):
                pass
            
            case (
                ReturnInstruction(expr)
                | SetVariableInstruction(_, expr)
                | NotExpression(expr)
                | UnaryExpression(expr)
                | AwaitExpression(expr)
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
            
            case FunctionExpression(args, body):
                self.visit_scope(args, body)
            
            case _:
                raise NotImplementedError(f'Unsupported instruction {type(instruction)}')
