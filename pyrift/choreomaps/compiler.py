from collections.abc import Generator, Iterable
from contextlib import contextmanager

from pyrift.choreomaps.tag import Tag

from .analysis import Analysis, ChoreomapAnalyzer, Scope, VarType
from .choreomap import Choreomap
from .enum import BinaryOperator, ComparisonMode
from .external import ExternalArgType, ExternalExpression, ExternalValue
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
    LogInstruction,
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


class ChoreomapCompiler:
    def __init__(self):
        self.streams: list[list[BaseEvent]] = []
        self.analysis: Analysis = Analysis(())
        self.externals: dict[str, ExternalValue] = {}
        self.scope: Scope = Scope((), (), 0)
        self.stream: list[BaseEvent] = []
        self.temp_index = 0
    
    def add_event(self, event: BaseEvent) -> None:
        self.stream.append(event)
    
    def lookup(self, name: str) -> tuple[int, VarType]:
        index = 0
        for i in range(len(self.scope.vars)):
            var_type = self.scope.types[i]
            if self.scope.vars[i] == name:
                return index, var_type
            if var_type in (VarType.LOCAL, VarType.CAPTURED, VarType.NONLOCAL):
                index += 2
        raise ValueError(f'Unknown variable {name}.')
    
    def allocate(self, *values: Value) -> Value:
        ref = VariableValue("$REF")
        name = NumberString(ref)
        # increment the heap counter
        self.add_event(SetVariableEvent("$REF", MathValue(ref, 1, BinaryOperator.ADD)))
        # copy in each value
        for i, value in enumerate(values):
            self.add_event(SetArrayEvent(name, index=i, value=value))
        return ref
    
    @contextmanager
    def new_scope(self) -> Generator[int]:
        # store old values
        old_scope = self.scope
        old_stream = self.stream
        old_temp_index = self.temp_index
        
        # make new stream
        scope = self.analysis.scopes[len(self.streams)]
        self.scope = scope
        self.stream = []
        self.streams.append(self.stream)
        
        # handle argument initialization
        tag_index = 0
        value_index = 1
        nl_tag_index = 1
        nl_value_index = 3
        for i, type in enumerate(scope.types):
            match type:
                # load directly from globals into locals array
                case VarType.LOCAL if i < scope.argc:
                    tag = ArrayValue("$ARGS", tag_index)
                    value = ArrayValue("$ARGS", value_index)
                
                # copy to the heap and save a reference in locals
                case VarType.CAPTURED if i < scope.argc:
                    tag = Tag.NONE
                    value = self.allocate(ArrayValue("$ARGS", tag_index), ArrayValue("$ARGS", value_index))
                
                # allocate uninitialized heap space for captured variables
                case VarType.CAPTURED:
                    tag = Tag.NONE
                    value = self.allocate()
                
                # load nonlocal arguments from environment global
                case VarType.NONLOCAL:
                    tag = ArrayValue("$ENV", nl_tag_index)
                    value = ArrayValue("$ENV", nl_value_index)
                    nl_tag_index += 2
                    nl_value_index += 2
                
                # the remaining variables don't get stored in the locals array
                case _:
                    continue
            
            self.add_event(SetArrayEvent(None, tag_index, tag))
            self.add_event(SetArrayEvent(None, value_index, value))
            self.temp_index += 2
            tag_index += 2
            value_index += 2
        
        # set default return value to None
        self.add_event(SetVariableEvent("$RTAG", Tag.NONE))
        self.add_event(SetVariableEvent("$RETURN", 0))
        
        # execute inner code
        yield len(self.streams) - 1 # id of stream
        
        if self.scope is not scope:
            raise ValueError('Scope nesting invariant was violated. This should only happen if scopes are being created manually.')
        
        # restore old values
        self.scope = old_scope
        self.temp_index = old_temp_index
        self.stream = old_stream
    
    def compile(self, script: Script, externals: dict[str, ExternalValue]):
        analysis = ChoreomapAnalyzer().analyze(script)
        self.analysis = analysis
        self.externals = externals
        
        self.visit_stream(script.instructions)
        
        streams: list[Stream] = []
        for i, stream in enumerate(self.streams):
            # stream id is 1-indexed
            streams.append(Stream(i + 1, tuple(stream)))
        
        # TODO: actually set the properties properly
        return Choreomap(
            streams=tuple(streams),
            input_rating_definitions=(),
            main_id=1
        )
    
    
    def visit_stream(self, nodes: Iterable[BaseInstruction]):
        with self.new_scope() as scope_id:
            for node in nodes:
                self.visit_inst(node)
        return scope_id
    
    
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
                
                yes_index = len(self.stream)
                for inst in yes:
                    self.visit_inst(inst)
                
                self.add_event(BaseEvent()) # placeholder jump
                
                no_index = len(self.stream)
                for inst in no:
                    self.visit_inst(inst)
                
                end_index = len(self.stream)
                self.stream[yes_index - 1] = JumpEvent(IfValue(condition, yes_index, no_index))
                self.stream[no_index - 1] = JumpEvent(end_index)
            
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
                # TODO: LOAD CAPTURED VARIABLES
                stream_id = self.visit_stream(instructions)
                return Tag.FUNCTION, stream_id
                
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
                # since visit_value can add events, we need to use control flow
                # otherwise, we'd always be evaluating both branches
                tag_index = self.temp_index
                value_index = self.temp_index + 1
                self.temp_index += 2
                
                self.add_event(BaseEvent()) # placeholder jump
                
                yes_index = len(self.stream)
                ytag, yes = self.visit_value(yes)
                self.add_event(SetArrayEvent(None, tag_index, ytag))
                self.add_event(SetArrayEvent(None, value_index, yes))
                
                self.add_event(BaseEvent()) # placeholder jump
                
                no_index = len(self.stream)
                ntag, no = self.visit_value(no)
                self.add_event(SetArrayEvent(None, tag_index, ntag))
                self.add_event(SetArrayEvent(None, value_index, no))
                
                end_index = len(self.stream)
                condition = self.visit_condition(condition)
                self.stream[yes_index - 1] = JumpEvent(IfValue(condition, yes_index, no_index))
                self.stream[no_index - 1] = JumpEvent(end_index)
                
                return ArrayValue(None, tag_index), ArrayValue(None, value_index)
            
            case CallExpression(func, args):
                # TODO: verify tag
                tag, func = self.visit_value(func)
                
                if isinstance(func, ExternalValue):
                    external_args: list[Value | Condition | String] = []
                    if not len(args) == len(func.args):
                        raise ValueError(f'Argument count mismatch for external function {func.func.__name__}. Expected {len(func.args)}, got {len(args)}')
                    for arg, spec in zip(args, func.args):
                        match spec.type:
                            case ExternalArgType.VALUE:
                                _, value = self.visit_value(arg)
                                external_args.append(value)
                            case ExternalArgType.CONDITION:
                                condition = self.visit_condition(arg)
                                external_args.append(condition)
                            case ExternalArgType.STRING:
                                string = self.visit_str(arg)
                                external_args.append(string)
                    expr = func.func(*external_args)
                    return self.visit_expr(expr)
                
                for i, arg in enumerate(args):
                    tag, value = self.visit_value(arg)
                    self.add_event(SetArrayEvent("$ARGS", 2 * i, tag))
                    self.add_event(SetArrayEvent("$ARGS", 2 * i + 1, value))
                # synchronous functions don't need a ref
                self.add_event(StartStreamEvent(func, 0, immediate=True))
                
                tag_index = self.temp_index
                value_index = self.temp_index + 1
                self.temp_index += 2 # TODO: HELPER FUNCTION FOR TEMPS
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
                operands = tuple(self.visit_value(operand)[1] for operand in operands)
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
