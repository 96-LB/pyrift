from collections.abc import Generator, Iterable
from contextlib import contextmanager

from pyrift.choreomaps.tag import Tag

from .analysis import Analysis, ChoreomapAnalyzer, ScopeInfo, VarType
from .choreomap import Choreomap
from .enum import BinaryOperator, ComparisonMode
from .external import ExternalArgType, ExternalExpression, ExternalValue
from .ir.expression import (
    AndExpression,
    BaseExpression,
    BinaryExpression,
    BooleanExpression,
    CallExpression,
    CompareExpression,
    FunctionExpression,
    IfExpression,
    JoinExpression,
    NumberExpression,
    OrExpression,
    StringExpression,
    UnaryExpression,
    VariableExpression,
)
from .ir.instruction import (
    BaseInstruction,
    IfInstruction,
    LogInstruction,
    NullInstruction,
    ReturnInstruction,
    SetVariableInstruction,
)
from .ir.script import Script
from .nodes import (
    AndCondition,
    ArrayValue,
    BaseCondition,
    BaseEvent,
    BaseString,
    BaseValue,
    CompareCondition,
    Condition,
    IfString,
    IfValue,
    JoinString,
    JumpEvent,
    LogEvent,
    MathValue,
    NumberString,
    OrCondition,
    SetArrayEvent,
    SetArrayStringEvent,
    SetVariableEvent,
    StartStreamEvent,
    StopStreamEvent,
    Stream,
    String,
    UnaryValue,
    Value,
    VariableValue,
)


class Scope:
    def __init__(self, id: int, info: ScopeInfo):
        self.id: int = id
        self.info = info
        self.events: list[BaseEvent] = []
        self.temp_index: int = 0
        for type in info.types:
            if type in (VarType.LOCAL, VarType.NONLOCAL, VarType.CAPTURED):
                self.temp_index += 2
    
    def temp(self):
        self.temp_index += 1
        return self.temp_index - 1


class ChoreomapCompiler:
    def __init__(self):
        self.streams: list[Scope] = []
        self.analysis: Analysis = Analysis(())
        self.externals: dict[str, ExternalValue] = {}
        self.scope: Scope = Scope(0, ScopeInfo((), (), 0))
    
    def add_event(self, event: BaseEvent) -> None:
        self.scope.events.append(event)
    
    def lookup(self, name: str) -> tuple[int, VarType]:
        index = 0
        for i in range(len(self.scope.info.vars)):
            var_type = self.scope.info.types[i]
            if self.scope.info.vars[i] == name:
                return index, var_type
            if var_type in (VarType.LOCAL, VarType.CAPTURED, VarType.NONLOCAL):
                index += 2
        raise ValueError(f'Unknown variable {name}.')
    
    def allocate(self, *values: BaseValue) -> BaseValue:
        ref = VariableValue("$REF")
        name = NumberString(ref)
        # increment the heap counter
        self.add_event(SetVariableEvent("$REF", MathValue(ref, 1, BinaryOperator.ADD)))
        # copy in each value
        for i, value in enumerate(values):
            self.add_event(SetArrayEvent(name, index=i, value=value))
        return ref
    
    @contextmanager
    def new_scope(self) -> Generator[Scope]:
        # prepare new scope object
        id = len(self.streams)
        scope = Scope(id + 1, self.analysis.scopes[id]) # streams are 1-indexed
        self.streams.append(scope)
        old, self.scope = self.scope, scope
        
        # load arguments from globals
        for i in range(scope.info.argc):
            tag_index = 2 * i
            value_index = 2 * i + 1
            tag = ArrayValue("$ARGS", tag_index)
            value = ArrayValue("$ARGS", value_index)
            match scope.info.types[i]:
                case VarType.LOCAL:
                    # copy tag and variable to locals
                    scope.events.append(SetArrayEvent(None, tag_index, tag))
                    scope.events.append(SetArrayEvent(None, value_index, value))
                case VarType.CAPTURED:
                    # copy argument to the heap and save a reference in locals
                    ref = self.allocate(tag, value)
                    scope.events.append(SetArrayEvent(None, tag_index, Tag.NONE))
                    scope.events.append(SetArrayEvent(None, value_index, ref))
                case _:
                    raise NotImplementedError(f'Unsupported argument type for argument {scope.info.vars[i]}: {scope.info.types[i]}')
        
        # set default return value to None
        scope.events.append(SetVariableEvent("$RTAG", Tag.NONE))
        scope.events.append(SetVariableEvent("$RETURN", 0))
        
        yield scope # execute inner code
        
        self.scope = old
    
    def compile(self, script: Script, externals: dict[str, ExternalValue]):
        analysis = ChoreomapAnalyzer().analyze(script)
        self.analysis = analysis
        self.externals = externals
        
        self.visit_stream(script.instructions)
        
        streams: list[Stream] = []
        for stream in self.streams:
            streams.append(Stream(
                stream.id,
                tuple(stream.events),
                _vars=stream.info.vars
            ))
        
        # TODO: actually set the properties properly
        return Choreomap(
            streams=tuple(streams),
            input_rating_definitions=(),
            main_id=1
        )
    
    
    def visit_stream(self, nodes: Iterable[BaseInstruction]):
        with self.new_scope() as scope:
            for node in nodes:
                self.visit_inst(node)
        return scope
    
    
    def visit_inst(self, node: BaseInstruction) -> None:
        match node:
            case NullInstruction():
                pass
            
            case BaseExpression():
                self.visit_expr(node)
            
            case SetVariableInstruction(name, expr):
                index, var_type = self.lookup(name)
                
                tag, value = self.visit_value(expr)
                match var_type:
                    case VarType.LOCAL:
                        # set the value in the locals array
                        self.add_event(SetArrayEvent(None, index, tag))
                        self.add_event(SetArrayEvent(None, index + 1, value))
                    case VarType.CAPTURED | VarType.NONLOCAL:
                        # the locals array contains a ref to the heap -- set the value there
                        ref = NumberString(ArrayValue(None, index + 1))
                        self.add_event(SetArrayEvent(ref, 0, tag))
                        self.add_event(SetArrayEvent(ref, 1, value))
                    case VarType.GLOBAL:
                        # set the global directly
                        self.add_event(SetVariableEvent("TAG$" + name, tag))
                        self.add_event(SetVariableEvent(name, value))
                    case VarType.EXTERNAL:
                        raise NotImplementedError('Setting external variables is unsupported.')
            
            case IfInstruction(condition, yes, no):
                condition = self.visit_condition(condition)
                
                self.add_event(BaseEvent()) # placeholder jump
                
                yes_index = len(self.scope.events)
                for inst in yes:
                    self.visit_inst(inst)
                
                self.add_event(BaseEvent()) # placeholder jump
                
                no_index = len(self.scope.events)
                for inst in no:
                    self.visit_inst(inst)
                
                end_index = len(self.scope.events)
                self.scope.events[yes_index - 1] = JumpEvent(IfValue(condition, yes_index, no_index))
                self.scope.events[no_index - 1] = JumpEvent(end_index)
            
            case ReturnInstruction(expr):
                tag, value = self.visit_value(expr)
                self.add_event(SetVariableEvent("$RTAG", tag))
                self.add_event(SetVariableEvent("$RETURN", value))
                self.add_event(StopStreamEvent())
            
            case LogInstruction(text):
                text = self.visit_str(text)
                self.add_event(LogEvent(text))
            
            case _:
                raise NotImplementedError(f'Unsupported instruction: {type(node)}')
    
    def visit_expr(self, node: BaseExpression) -> tuple[Value, Value | Condition | String]:
        match node:
            case NumberExpression(value):
                return Tag.NUMBER, value
            
            case BooleanExpression(value):
                return Tag.NUMBER, value
            
            case StringExpression(value):
                return Tag.STRING, value
            
            case FunctionExpression(args, instructions):
                stream = self.visit_stream(instructions)
                return Tag.FUNCTION, stream.id
                
            case VariableExpression(name):
                value_index, var_type = self.lookup(name)
                
                match var_type:
                    case VarType.LOCAL:
                        # get the value from the locals array
                        tag = ArrayValue(None, value_index)
                        value = ArrayValue(None, value_index + 1)
                        return tag, value
                    case VarType.CAPTURED | VarType.NONLOCAL:
                        # the locals array contains a ref to the heap -- get the value there
                        ref = NumberString(ArrayValue(None, value_index + 1))
                        tag = ArrayValue(ref, 0)
                        value = ArrayValue(ref, 1)
                    case VarType.GLOBAL:
                        # get the global directly
                        tag = VariableValue("TAG$" + name)
                        value = VariableValue(name)
                    case VarType.EXTERNAL:
                        if name not in self.externals:
                            raise ValueError(f'Unknown external variable {name}.')
                        tag = Tag.FUNCTION
                        value = self.externals[name]
                
                return tag, value
            
            case AndExpression(conditions):
                conditions = tuple(self.visit_condition(condition) for condition in conditions)
                return Tag.NUMBER, AndCondition(conditions)
            
            case OrExpression(conditions):
                conditions = tuple(self.visit_condition(condition) for condition in conditions)
                return Tag.NUMBER, OrCondition(conditions)
            
            case BinaryExpression(left, operator, right):
                ltag, left = self.visit_value(left)
                rtag, right = self.visit_value(right)
                match ltag, rtag:
                    case Tag.NUMBER, Tag.NUMBER:
                        return Tag.NUMBER, MathValue(left, right, operator)
                    case _: # TODO: a lot of cases
                        return Tag.NUMBER, MathValue(left, right, operator) # TODO: REMOVE
                        raise NotImplementedError(f'Binary operation between tags {type(ltag).__name__} and {type(rtag).__name__} is unsupported.')
            
            case UnaryExpression(expr, operator):
                tag, value = self.visit_value(expr)
                match tag:
                    case Tag.NUMBER:
                        return Tag.NUMBER, UnaryValue(value, operator)
                    case _:
                        raise NotImplementedError(f'Unary operation on tag {type(tag)} is unsupported.')
            
            case IfExpression(condition, yes, no):
                condition = self.visit_condition(condition)
                ytag, yes = self.visit_value(yes)
                ntag, no = self.visit_value(no)
                # TODO: optimize case where tags are equal, or condition is constant
                return IfValue(condition, ytag, ntag), IfValue(condition, yes, no)
            
            case CallExpression(func, args):
                # TODO: verify tag
                tag, func = self.visit_value(func)
                
                if isinstance(func, ExternalValue):
                    external_args: list[Value | Condition | String] = []
                    if not len(args) == len(func.args):
                        raise ValueError(f'Argument count mismatch for external function {func.func.__name__}. Expected {len(func.args)}, got {len(args)}')
                    for i in range(len(func.args)):
                        match func.args[i].type:
                            case ExternalArgType.VALUE:
                                tag, value = self.visit_value(args[i])
                                external_args.append(value)
                            case ExternalArgType.CONDITION:
                                condition = self.visit_condition(args[i])
                                external_args.append(condition)
                            case ExternalArgType.STRING:
                                string = self.visit_str(args[i])
                                external_args.append(string)
                    expr = func.func(*external_args)
                    return self.visit_expr(expr)
                
                for i, arg in enumerate(args):
                    tag, value = self.visit_value(arg)
                    self.add_event(SetArrayEvent("$ARGS", 2 * i, tag))
                    self.add_event(SetArrayEvent("$ARGS", 2 * i + 1, value))
                # synchronous functions don't need a ref
                self.add_event(StartStreamEvent(func, 0, immediate=True))
                
                tag_index = self.scope.temp()
                value_index = self.scope.temp()
                self.add_event(SetArrayEvent(None, tag_index, VariableValue("$RTAG")))
                self.add_event(SetArrayEvent(None, value_index, VariableValue("$RETURN")))
                return ArrayValue(None, tag_index), ArrayValue(None, value_index)
            
            case JoinExpression(strings):
                # TODO: verify tag
                strings = tuple(self.visit_str(string) for string in strings)
                return Tag.STRING, JoinString(strings)
            
            case CompareExpression(first, operands, operators):
                # TODO: verify tags
                _, first = self.visit_value(first)
                operands = tuple(self.visit_value(operand)[0] for operand in operands)
                assert 0 < len(operands)
                assert len(operands) == len(operators)
                
                if len(operators) == 1:
                    return Tag.NUMBER, CompareCondition(first, operands[0], operators[0])
                else:
                    conditions = tuple(
                        CompareCondition(first if i == 0 else operands[i - 1], operands[i], operators[i])
                        for i in range(len(operators))
                    )
                    return Tag.NUMBER, AndCondition(conditions)
            
            case ExternalExpression(events, tag, value):
                for event in events:
                    self.add_event(event)
                return tag, value
            
            case _:
                raise NotImplementedError(f'Unsupported expression: {type(node).__name__}')
    
    def visit_value(self, node: BaseExpression) -> tuple[Value, Value]:
        tag, value = self.visit_expr(node)
        match value:
            case BaseCondition() | bool():
                return Tag.NUMBER, IfValue(value, 1, 0)
            case BaseValue() | float() | int():
                return tag, value
            case BaseString() | str():
                ref = self.allocate()
                self.add_event(SetArrayStringEvent(NumberString(ref), value)) # TODO: THIS IS REALLY BAD
                return Tag.STRING, ref
    
    def visit_condition(self, node: BaseExpression) -> Condition:
        tag, value = self.visit_expr(node)
        match tag, value:
            case _, BaseCondition() | bool():
                return value
            case Tag.NUMBER, BaseValue() | float() | int():
                return CompareCondition(value, 0, ComparisonMode.NOT_EQUAL)
            case _, BaseString() | str():
                raise NotImplementedError('#TODO: implement strings')
            case _: # TODO: a lot of cases
                return CompareCondition(value, 0, ComparisonMode.NOT_EQUAL) # TODO: REMOVE
                raise NotImplementedError(f'Missing case when trying to cast value to condition: tag={type(tag).__name__}, value={type(value).__name__}.')
    
    def visit_str(self, node: BaseExpression):
        tag, value = self.visit_expr(node)
        match tag, value:
            case _, BaseCondition() | bool():
                return IfString(value, "True", "False")
            case Tag.NUMBER, BaseValue() | float() | int():
                return NumberString(value)
            case _, BaseValue() | float() | int(): # TODO: a lot of cases
                return NumberString(value) # TODO: REMOVE
                raise NotImplementedError(f'Missing case when trying to cast value to condition: tag={type(tag).__name__}, value={type(value).__name__}.')
            case _, BaseString() | str():
                return value
