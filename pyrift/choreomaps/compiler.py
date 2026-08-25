from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from functools import wraps

from .analysis import Analysis, ChoreomapAnalyzer, Scope, VarType
from .backend import (
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
    MathValue,
    NumberString,
    OrCondition,
    SetArrayEvent,
    SetArrayStringEvent,
    SetVariableEvent,
    StartStreamEvent,
    Stream,
    String,
    TaggedValue,
    UnaryValue,
    Value,
    VariableValue,
    WaitEvent,
)
from .choreomap import Choreomap
from .context import StreamContext
from .enum import BinaryOperator, ComparisonMode
from .external import ExternalArgType, ExternalValue
from .ir import (
    AndExpression,
    AwaitExpression,
    BaseExpression,
    BaseInstruction,
    BinaryExpression,
    BooleanExpression,
    CallExpression,
    CompareExpression,
    DeclareVariablesInstruction,
    FunctionExpression,
    IfExpression,
    IfInstruction,
    JoinExpression,
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
from .vars import Tag


class ChoreomapCompiler:
    def __init__(self):
        self.streams: list[StreamContext] = []
        self.analysis: Analysis = Analysis(())
        self.externals: dict[str, ExternalValue] = {}
        self.context: StreamContext = StreamContext(Scope.empty())
    
    def add_event(self, event: BaseEvent) -> None:
        self.context.add_event(event)
    
    def lookup(self, name: str) -> tuple[int, VarType]:
        index = 0
        for i in range(len(self.context.scope.vars)):
            var_type = self.context.scope.types[i]
            if self.context.scope.vars[i] == name:
                return index, var_type
            if var_type in (VarType.LOCAL, VarType.CAPTURED, VarType.NONLOCAL):
                index += 2
        raise ValueError(f'Unknown variable {name}.')
    
    def allocate(self, *values: Value) -> Value:
        ref = VariableValue('$REF')
        name = NumberString(ref)
        # increment the heap counter
        self.add_event(SetVariableEvent('$REF', MathValue(ref, 1, BinaryOperator.ADD)))
        # copy in each value
        for i, value in enumerate(values):
            self.add_event(SetArrayEvent(name, index=i, value=value))
        return ref
    
    def deref(self, ref: Value, index: Value) -> Value:
        return ArrayValue(NumberString(ref), index)
    
    @contextmanager
    def new_scope(self, is_async: bool) -> Generator[int]:
        # store old context and make new one
        old_context = self.context
        scope = self.analysis.scopes[len(self.streams)]
        context = StreamContext(scope)
        self.context = context
        self.streams.append(context)
        
        # pointers for argument initialization
        env = VariableValue('$ENV')
        tag_index = 0
        value_index = 1
        nonlocal_index = 1
        
        # handle argument initialization
        for i, type in enumerate(scope.types):
            match type:
                # load directly from globals into locals array
                case VarType.LOCAL if i < scope.argc:
                    tag = ArrayValue('$ARGS', tag_index)
                    value = ArrayValue('$ARGS', value_index)
                
                # copy to the heap and save a reference in locals
                case VarType.CAPTURED if i < scope.argc:
                    tag = Tag.NONE
                    value = self.allocate(ArrayValue('$ARGS', tag_index), ArrayValue('$ARGS', value_index))
                
                # allocate uninitialized heap space for captured variables
                case VarType.CAPTURED:
                    tag = Tag.NONE
                    value = self.allocate()
                
                # load nonlocal arguments from environment global
                case VarType.NONLOCAL:
                    tag = Tag.NONE
                    value = self.deref(env, nonlocal_index)
                    nonlocal_index += 1
                
                # the remaining variables don't get stored in the locals array
                case _:
                    continue
            
            self.add_event(SetArrayEvent(None, tag_index, tag))
            self.add_event(SetArrayEvent(None, value_index, value))
            self.context.temp_index += 2
            tag_index += 2
            value_index += 2
        
        # set default return value to None
        # async functions allocate a coroutine object to store their return value
        if is_async:
            async_pointer = self.allocate(0, Tag.NONE, 0, 0)
            self.context.make_async(async_pointer)
        
        # execute inner code
        yield len(self.streams) # id of stream
        
        if self.context is not context:
            raise ValueError('Scope nesting invariant was violated. This should only happen if scopes are being created manually.')
        
        # finalize stream and restore old values
        context.return_value()
        self.context = old_context
    
    @staticmethod
    def push_stack[T: BaseInstruction, R](func: Callable[[ChoreomapCompiler, T], R]) -> Callable[[ChoreomapCompiler, T], R]:
        @wraps(func) # TODO: import decorates_self?
        def wrapper(self: ChoreomapCompiler, inst: T):
            self.context.push_stack(inst, len(self.streams))
            output = func(self, inst)
            self.context.pop_stack()
            return output
        return wrapper
    
    def compile(self, script: Script, externals: dict[str, ExternalValue]):
        analysis = ChoreomapAnalyzer().analyze(script)
        self.analysis = analysis
        self.externals = externals
        
        self.visit_stream(script.instructions, is_async=False)
        
        # TODO: actually set the properties properly
        streams = tuple(Stream(i + 1, tuple(stream.events)) for i, stream in enumerate(self.streams))
        return Choreomap(
            streams=streams,
            input_rating_definitions=(),
            main_id=1
        )
    
    def visit_stream(self, nodes: Iterable[BaseInstruction], is_async: bool):
        with self.new_scope(is_async) as scope_id:
            for node in nodes:
                self.visit_inst(node)
        return scope_id
    
    @push_stack
    def visit_inst(self, node: BaseInstruction) -> None:
        match node:
            case NullInstruction() | DeclareVariablesInstruction():
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
                        self.add_event(SetVariableEvent('TAG$' + name, tag))
                        self.add_event(SetVariableEvent(name, value))
                    case VarType.EXTERNAL:
                        raise NotImplementedError('Setting external variables is unsupported.')
            
            case IfInstruction(condition, yes, no):
                self.context.upgrade_timekeeping()
                condition = self.visit_condition(condition)
                
                self.add_event(BaseEvent()) # placeholder jump
                yes_index = len(self.context.events)
                
                for inst in yes:
                    self.visit_inst(inst)
                
                self.add_event(BaseEvent()) # placeholder jump
                no_index = len(self.context.events)
                
                for inst in no:
                    self.visit_inst(inst)
                
                end_index = len(self.context.events)
                self.context.replace_event(yes_index - 1, JumpEvent(IfValue(condition, yes_index, no_index)))
                self.context.replace_event(no_index - 1, JumpEvent(end_index))
            
            case ReturnInstruction(expr):
                tag, value = self.visit_value(expr)
                self.context.return_value((tag, value))
            
            case _:
                raise NotImplementedError(f'Unsupported instruction: {type(node)}')
    
    @push_stack
    def visit_expr(self, node: BaseExpression) -> TaggedValue:
        match node:
            case NumberExpression(value):
                return Tag.NUMBER, value
            
            case BooleanExpression(value):
                return Tag.NUMBER, value
            
            case StringExpression(value):
                return Tag.STRING, value
            
            case FunctionExpression(args, instructions, is_async):
                stream_id = self.visit_stream(instructions, is_async)
                scope = self.analysis.scopes[stream_id - 1] # stream id's are 1-indexed
                
                # copy stream id and captured variables into the closure environment
                values: list[Value] = [stream_id]
                for var, var_type in zip(scope.vars, scope.types):
                    if var_type is VarType.NONLOCAL:
                        value_index = self.lookup(var)[0] + 1 # lookup returns the tag index
                        values.append(ArrayValue(None, value_index))
                
                # create and return the closure
                ref = self.allocate(*values)
                return Tag.FUNCTION, ref
                
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
                        ref = ArrayValue(None, value_index + 1)
                        tag = self.deref(ref, 0)
                        value = self.deref(ref, 1)
                    case VarType.GLOBAL:
                        # get the global directly
                        tag = VariableValue('TAG$' + name)
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
                self.context.upgrade_timekeeping()
                tag_index, value_index = self.context.allocate_temp()
                
                self.add_event(BaseEvent()) # placeholder jump
                yes_index = len(self.context.events)
                
                ytag, yes = self.visit_value(yes)
                self.add_event(SetArrayEvent(None, tag_index, ytag))
                self.add_event(SetArrayEvent(None, value_index, yes))
                
                self.add_event(BaseEvent()) # placeholder jump
                no_index = len(self.context.events)
                
                ntag, no = self.visit_value(no)
                self.add_event(SetArrayEvent(None, tag_index, ntag))
                self.add_event(SetArrayEvent(None, value_index, no))
                
                end_index = len(self.context.events)
                condition = self.visit_condition(condition)
                self.context.replace_event(yes_index - 1, JumpEvent(IfValue(condition, yes_index, no_index)))
                self.context.replace_event(no_index - 1, JumpEvent(end_index))
                
                return ArrayValue(None, tag_index), ArrayValue(None, value_index)
            
            case CallExpression(func, args):
                # TODO: verify tag
                tag, ref = self.visit_value(func)
                
                if isinstance(ref, ExternalValue):
                    external_args: list[Value | Condition | String] = []
                    if not len(args) == len(ref.args):
                        raise ValueError(f'Argument count mismatch for external function {ref.func.__name__}. Expected {len(ref.args)}, got {len(args)}')
                    for arg, spec in zip(args, ref.args):
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
                    return ref.func(self.context, *external_args)
                
                # copy arguments into register for callee function
                for i, arg in enumerate(args):
                    tag, value = self.visit_value(arg)
                    self.add_event(SetArrayEvent('$ARGS', 2 * i, tag))
                    self.add_event(SetArrayEvent('$ARGS', 2 * i + 1, value))
                
                # set the environment pointer so the function can load the closure
                self.add_event(SetVariableEvent('$ENV', ref))
                
                # synchronous functions don't need a ref_id because they finish instantly
                stream_id = self.deref(ref, 0)
                self.add_event(StartStreamEvent(stream_id, 0, immediate=True))
                
                tag_index, value_index = self.context.allocate_temp()
                self.add_event(SetArrayEvent(None, tag_index, VariableValue('$RTAG')))
                self.add_event(SetArrayEvent(None, value_index, VariableValue('$RETURN')))
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
            
            case AwaitExpression(expr):
                if not self.context.async_ref:
                    raise ValueError('Await expression encountered in synchronous context.')
                
                tag, value = self.visit_value(expr)
                if isinstance(value, ExternalValue):
                    return tag, value
                
                match tag:
                    case Tag.COROUTINE:
                        finished = self.deref(value, 0)
                        rtag = self.deref(value, 1)
                        rval = self.deref(value, 2)
                        t = self.deref(value, 3)
                        condition = CompareCondition(finished, 0, ComparisonMode.NOT_EQUAL)
                        self.add_event(WaitEvent(condition))
                        self.context.wait(t) # update local timekeeping
                        return rtag, rval
                    
                    case Tag(tag) | int(tag):
                        # TODO: maybe error here
                        return tag, value
                    
                    case tag: # TODO: generalize if statements? we'll need to do this runtime check in a lot of places
                        # dynamic runtime check
                        self.context.upgrade_timekeeping()
                        tag_index, value_index = self.context.allocate_temp()
                        
                        self.add_event(BaseEvent()) # placeholder jump
                        yes_index = len(self.context.events)
                        
                        finished = self.deref(value, 0)
                        rtag = self.deref(value, 1)
                        rval = self.deref(value, 2)
                        t = self.deref(value, 3)
                        condition = CompareCondition(finished, 0, ComparisonMode.NOT_EQUAL)
                        self.add_event(WaitEvent(condition))
                        self.context.wait(t) # update local timekeeping
                        
                        self.add_event(SetArrayEvent(None, tag_index, rtag))
                        self.add_event(SetArrayEvent(None, value_index, rval))
                        
                        self.add_event(BaseEvent()) # placeholder jump
                        no_index = len(self.context.events)
                        
                        self.add_event(SetArrayEvent(None, tag_index, tag))
                        self.add_event(SetArrayEvent(None, value_index, value))
                        
                        end_index = len(self.context.events)
                        self.context.replace_event(yes_index - 1, JumpEvent(IfValue(condition, yes_index, no_index)))
                        self.context.replace_event(no_index - 1, JumpEvent(end_index))
                        
                        return ArrayValue(None, tag_index), ArrayValue(None, value_index)
            
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
                return IfString(value, 'True', 'False')
            case Tag.NUMBER, BaseValue() | float() | int():
                return NumberString(value)
            case _, BaseValue() | float() | int(): # TODO: a lot of cases
                return NumberString(value) # TODO: REMOVE
                raise NotImplementedError(f'Missing case when trying to cast value to condition: tag={type(tag).__name__}, value={type(value).__name__}.')
            case _, BaseString() | str():
                return value
