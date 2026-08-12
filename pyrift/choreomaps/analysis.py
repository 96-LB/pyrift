from collections.abc import Generator, Iterable
from contextlib import contextmanager

from pyrift.choreomaps.ir.expression import (
    BinaryExpression,
    BooleanExpression,
    CallExpression,
    CompareExpression,
    FormatExpression,
    FunctionExpression,
    IfExpression,
    JoinExpression,
    NotExpression,
    NullExpression,
    NumberExpression,
    StringExpression,
    UnaryExpression,
    VariableExpression,
)
from pyrift.choreomaps.ir.instruction import (
    BaseInstruction,
    IfInstruction,
    LogInstruction,
    NullInstruction,
    ReturnInstruction,
    SetVariableInstruction,
)
from pyrift.choreomaps.ir.script import Script
from pyrift.jobj import JList, JObj


class Analysis(JObj):
    scopes: JList[Scope]

class Scope(JObj):
    locals: JList[str]
    refs: JList[str]

class ScopeAnalyzer:
    def __init__(self, parent: ScopeAnalyzer | None = None):
        self.parent: ScopeAnalyzer | None = parent
        self.vars: dict[str, bool] = {} # True if lives on the heap
    
    def declare(self, name: str):
        if name not in self.vars:
            self.vars[name] = False
        elif self.vars[name]:
            raise ValueError('Modifying a nonlocal variable is unsupported.')
    
    def capture(self, name: str):
        self.vars[name] = True
    
    def to_scope(self):
        return Scope(
            locals=tuple(var for var in self.vars if not self.vars[var]),
            refs=tuple(var for var in self.vars if self.vars[var])
        )


class ChoreomapAnalyzer:
    def __init__(self):
        self.scopes: dict[int, ScopeAnalyzer] = {}
        self.scope: ScopeAnalyzer = ScopeAnalyzer()
    
    def resolve(self, name: str):
        scope = self.scope
        while scope:
            if name in scope.vars:
                if scope != self.scope:
                    scope.capture(name)
                return scope
            scope.capture(name)
            scope = scope.parent
        raise ValueError(f'Unbound variable: {name}')
    
    @contextmanager
    def new_scope(self, id: int, args: Iterable[str] = ()) -> Generator[ScopeAnalyzer]:
        parent = self.scope
        scope = ScopeAnalyzer(parent)
        for arg in args:
            scope.declare(arg)
        
        self.scopes[id] = scope
        self.scope = scope
        yield scope
        self.scope = parent
    
    def analyze(self, script: Script):
        with self.new_scope(1):
            self.declare_vars(script.instructions)
            for inst in script.instructions:
                self.visit_inst(inst)
        return Analysis(tuple(self.scopes[i + 1].to_scope() for i in range(len(self.scopes))))
    
    def declare_vars(self, instructions: JList[BaseInstruction]):
        for inst in instructions:
            if isinstance(inst, SetVariableInstruction):
                self.scope.declare(inst.name)
    
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
                self.resolve(name)
            
            case SetVariableInstruction(name, expr):
                self.scope.declare(name)
                self.visit_inst(expr)
            
            case FunctionExpression(id, args, body):
                with self.new_scope(id, args):
                    self.declare_vars(body)
                    for inst in body:
                        self.visit_inst(inst)
                
            case _:
                raise NotImplementedError(f'Unsupported instruction {type(instruction)}')
