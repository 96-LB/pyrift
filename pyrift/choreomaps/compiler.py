from collections.abc import Generator, Iterable
from contextlib import contextmanager
from functools import reduce
from typing import Literal

from pyrift.util.decorators import decorates
from pyrift.util.typing import F

from .analysis import Analysis, ChoreomapAnalyzer, Scope, VarType
from .backend import (
    AndCondition,
    ArrayString,
    ArrayValue,
    BaseCondition,
    BaseEvent,
    BaseString,
    BaseValue,
    CompareCondition,
    Condition,
    IfEvent,
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
from .backend.string import FormatString
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
    ListExpression,
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


@decorates
def push_stack[T: BaseInstruction, R](func: F[[ChoreomapCompiler, T], R], self: ChoreomapCompiler, inst: T) -> R:
    # TODO: i would like this to be a static method but pyright disagrees
    self.context.push_stack(inst)
    output = func(self, inst)
    self.context.pop_stack()
    return output

class ChoreomapCompiler:
    def __init__(self):
        self.streams: list[StreamContext] = []
        self.analysis: Analysis = Analysis(())
        self.externals: dict[str, ExternalValue] = {}
        self.context: StreamContext = StreamContext(Scope((), (), 0))
        self.active = True # gets set to false while in dynamic match
        self.match_output: TaggedValue = Tag.NONE, 0 # output of latest match statement
    
    def add_event(self, event: BaseEvent) -> None:
        if self.active:
            self.context.add_event(event)
    
    @contextmanager
    def match(self, value: Value):
        simple = isinstance(value, (Tag, int))
        
        matching = False
        possible_tags = {value} if simple else {tag for tag in Tag} # TODO: better analysis of what tags are possible
        matched_tags = set[Tag]()
        jumps: list[tuple[int, Condition]] = []
        
        @contextmanager
        def case(*tags: Tag):
            nonlocal matching
            
            if matching:
                raise ValueError('Cases cannot be nested.')
            
            if not tags:
                tags = tuple(tag for tag in Tag if tag not in matched_tags)
            
            for tag in set(tags) & possible_tags:
                if tag in matched_tags:
                    raise ValueError(f'Tag {tag} has already been matched.')
                else:
                    matched_tags.add(tag)
            
            if not simple and matched_tags:
                # add a jump instruction if this branch succeeded
                conditions = [CompareCondition(value, tag, ComparisonMode.NOT_EQUAL) for tag in matched_tags]
                condition = conditions[0] if len(conditions) == 1 else AndCondition(tuple(conditions))
                jumps.append((len(self.context), condition))
                self.context.add_event(BaseEvent()) # placeholder jump
            
            matching = True
            old_active = self.active
            self.active = bool(matched_tags)
            yield
            self.active = old_active
            matching = False
        
        if simple:
            yield case
        else:
            self.context.begin_control_flow()
            tag_index, value_index = self.context.allocate_temp()
            yield case
            self.match_output = (ArrayValue(None, tag_index), ArrayValue(None, value_index))
            for i, (index, condition) in enumerate(jumps):
                jump_index = jumps[i + 1][0] if i + 1 < len(jumps) else len(self.context)
                self.context.replace_event(index, IfEvent(condition, JumpEvent(jump_index), None))
        
        unmatched_tags = possible_tags - matched_tags
        if unmatched_tags:
            raise ValueError(f'The following tags were not matched: {', '.join(str(tag) for tag in unmatched_tags)}')
    
    def match_return(self, tag: Value, value: Value):
        if self.active:
            self.match_output = tag, value
    
    def allocate(self, *values: Value) -> Value:
        ref = VariableValue('$REF')
        name = NumberString(ref)
        # increment the heap counter
        self.add_event(SetVariableEvent('$REF', MathValue(ref, 1, BinaryOperator.ADD)))
        # copy in each value
        for i, value in enumerate(values):
            self.add_event(SetArrayEvent(name, index=i, value=value))
        return ref
    
    def allocate_to_temp(self, *values: Value) -> tuple[Literal[Tag.NONE], Value]:
        ref = self.allocate(*values)
        tag_index, value_index = self.context.allocate_temp()
        self.add_event(SetArrayEvent(None, tag_index, Tag.NONE))
        self.add_event(SetArrayEvent(None, value_index, ref))
        return Tag.NONE, ArrayValue(None, value_index)
    
    def allocate_string(self, string: String) -> tuple[Literal[Tag.STRING], Value]:
        ref = self.allocate()
        tag_index, value_index = self.context.allocate_temp()
        self.add_event(SetArrayStringEvent(NumberString(ref), string))
        self.add_event(SetArrayEvent(None, tag_index, Tag.STRING))
        self.add_event(SetArrayEvent(None, value_index, ref))
        return Tag.STRING, ArrayValue(None, value_index)
    
    def allocate_array(self, *tagged_values: tuple[Value, Value]) -> tuple[Literal[Tag.ARRAY], Value]:
        # flatten tagged values into a single array
        values = (value for tagged_value in tagged_values for value in tagged_value)
        ref = self.allocate(*values)
        tag_index, value_index = self.context.allocate_temp()
        self.add_event(SetArrayEvent(None, tag_index, Tag.ARRAY))
        self.add_event(SetArrayEvent(None, value_index, ref))
        return Tag.ARRAY, ArrayValue(None, value_index)
        # TODO: allocation can be made more DRY
    
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
            _, async_pointer = self.allocate_to_temp(0, Tag.NONE, 0, 0)
            self.context.make_async(async_pointer)
        
        # execute inner code
        yield len(self.streams) # id of stream
        
        if self.context is not context:
            raise ValueError('Scope nesting invariant was violated. This should only happen if scopes are being created manually.')
        
        # finalize stream and restore old values
        context.return_value(Tag.NONE, 0)
        self.context = old_context
    
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
                index, var_type = self.context.lookup(name)
                
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
                self.context.begin_control_flow()
                condition = self.visit_condition(condition)
                
                self.add_event(BaseEvent()) # placeholder jump
                yes_index = len(self.context)
                
                for inst in yes:
                    self.visit_inst(inst)
                
                self.add_event(BaseEvent()) # placeholder jump
                no_index = len(self.context)
                
                for inst in no:
                    self.visit_inst(inst)
                
                end_index = len(self.context)
                self.context.replace_event(yes_index - 1, JumpEvent(IfValue(condition, yes_index, no_index)))
                self.context.replace_event(no_index - 1, JumpEvent(end_index))
            
            case ReturnInstruction(expr):
                tag, value = self.visit_value(expr)
                self.context.return_value(tag, value)
            
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
                        value_index = self.context.lookup(var)[0] + 1 # lookup returns the tag index
                        values.append(ArrayValue(None, value_index))
                
                # create and return the closure
                _, ref = self.allocate_to_temp(*values) # TODO: this probably yields unnecessary allocations
                return Tag.FUNCTION, ref
                
            case VariableExpression(name):
                value_index, var_type = self.context.lookup(name)
                
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
                self.context.begin_control_flow()
                tag_index, value_index = self.context.allocate_temp()
                
                self.add_event(BaseEvent()) # placeholder jump
                yes_index = len(self.context)
                
                ytag, yes = self.visit_value(yes)
                self.add_event(SetArrayEvent(None, tag_index, ytag))
                self.add_event(SetArrayEvent(None, value_index, yes))
                
                self.add_event(BaseEvent()) # placeholder jump
                no_index = len(self.context)
                
                ntag, no = self.visit_value(no)
                self.add_event(SetArrayEvent(None, tag_index, ntag))
                self.add_event(SetArrayEvent(None, value_index, no))
                
                # TODO: we can do these jumps simpler i think
                end_index = len(self.context)
                condition = self.visit_condition(condition)
                self.context.replace_event(yes_index - 1, JumpEvent(IfValue(condition, yes_index, no_index)))
                self.context.replace_event(no_index - 1, JumpEvent(end_index))
                
                return ArrayValue(None, tag_index), ArrayValue(None, value_index)
            
            case CallExpression(func, args):
                # TODO: verify tag
                tag, ref = self.visit_value(func)
                
                if isinstance(ref, ExternalValue) and self.active:
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
                if not self.context.is_async:
                    raise ValueError('Await expression encountered in synchronous context.')
                
                tag, value = self.visit_value(expr)
                if isinstance(value, ExternalValue):
                    return tag, value
                
                with self.match(tag) as case:
                    with case(Tag.COROUTINE):
                        finished = self.deref(value, 0)
                        rtag = self.deref(value, 1)
                        rval = self.deref(value, 2)
                        t = self.deref(value, 3)
                        condition = CompareCondition(finished, 0, ComparisonMode.NOT_EQUAL)
                        self.add_event(WaitEvent(condition))
                        self.context.wait(t) # update local timekeeping
                        self.match_return(rtag, rval)
                    
                    with case():
                        self.match_return(tag, value)
                
                return self.match_output
            
            case ListExpression(exprs):
                # TODO: we can probably intern some lists
                _, ref = self.allocate_array(*(self.visit_value(expr) for expr in exprs))
                return Tag.ARRAY, ref # TODO: actually handle arrays
            
            case _:
                raise NotImplementedError(f'Unsupported expression: {type(node).__name__}')
    
    def visit_value(self, node: BaseExpression) -> tuple[Value, Value]:
        tag, value = self.visit_expr(node)
        match value:
            case BaseCondition():
                return Tag.NUMBER, IfValue(value, 1, 0)
            case BaseString() | str():
                # TODO: we should be interning strings
                return self.allocate_string(value)
            case BaseValue() | float() | int():
                return tag, value
    
    def visit_condition(self, node: BaseExpression) -> Condition:
        tag, value = self.visit_expr(node)
        match value:
            case bool() | float() | int() | str():
                return bool(value)
            
            case BaseCondition():
                return value
            
            case BaseString():
                # TODO: we should be interning strings
                _, ref = self.allocate_string(value)
                return CompareCondition(ArrayValue(NumberString(ref)), 0, ComparisonMode.NOT_EQUAL)
            
            case BaseValue():
                mapping = {
                    Tag.NONE: False,
                    Tag.NUMBER: CompareCondition(value, 0, ComparisonMode.NOT_EQUAL),
                    Tag.STRING: CompareCondition(ArrayValue(NumberString(value)), 0, ComparisonMode.NOT_EQUAL),
                    Tag.FUNCTION: True,
                    Tag.COROUTINE: True,
                    Tag.ARRAY: CompareCondition(ArrayValue(NumberString(value)), 0, ComparisonMode.NOT_EQUAL), # TODO: this is a length check, but arrays not implemented
                    Tag.OBJECT: True,
                }
                
                if isinstance(tag, Tag):
                    return mapping.get(tag, False)
                else:
                    conditions = tuple(
                        CompareCondition(tag, t, ComparisonMode.EQUAL)
                        if mapping[t] is True
                        else AndCondition((CompareCondition(tag, t, ComparisonMode.EQUAL), mapping[t]))
                        for t in Tag if mapping[t] is not False
                    )
                    return OrCondition(conditions)
    
    def visit_str(self, node: BaseExpression) -> String:
        tag, value = self.visit_expr(node)
        match value:
            case bool() | str() | float() | int():
                return str(value)
            
            case BaseCondition():
                return IfString(value, 'True', 'False')
            
            case BaseString():
                return value
            
            case BaseValue():
                mapping = {
                    Tag.NONE: 'None',
                    Tag.NUMBER: NumberString(value),
                    Tag.STRING: ArrayString(NumberString(value)),
                    Tag.FUNCTION: FormatString('<function {0}>', (NumberString(value),)), # TODO: better string representations
                    Tag.COROUTINE: FormatString('<coroutine {0}>', (NumberString(value),)),
                    Tag.ARRAY: FormatString('<array {0}>', (NumberString(value),)),
                    Tag.OBJECT: FormatString('<object {0}>', (NumberString(value),)),
                }
                
                if isinstance(tag, Tag):
                    return mapping.get(tag, '<unknown>')
                else:
                    return reduce(
                        lambda acc, t: IfString(CompareCondition(tag, t, ComparisonMode.EQUAL), mapping[t], acc),
                        Tag,
                        '<unknown>'
                    )
