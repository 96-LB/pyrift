from collections.abc import Generator, Iterable
from contextlib import contextmanager
from functools import reduce
from typing import Concatenate

from pyrift.util.decorators import decorates
from pyrift.util.typing import F

from .analysis import Analysis, ChoreomapAnalyzer, VarType
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
from .context import DummyContext, Scope, StreamContext
from .external import ExternalCoroutine, ExternalObject
from .ir import (
    AwaitExpression,
    BaseExpression,
    BaseInstruction,
    BinaryExpression,
    BooleanExpression,
    BreakInstruction,
    CallExpression,
    CompareExpression,
    DeclareVariablesInstruction,
    FunctionExpression,
    IfExpression,
    IfInstruction,
    JoinExpression,
    ListExpression,
    LogicalExpression,
    NullExpression,
    NullInstruction,
    NumberExpression,
    ReturnInstruction,
    Script,
    SetVariableInstruction,
    StringExpression,
    UnaryExpression,
    VariableExpression,
    WhileInstruction,
)
from .vars import Tag


type CompilerObject = TaggedValue | Condition | String | ExternalObject | list[CompilerObject] | None

@decorates
def push_stack[**P, T: BaseInstruction, R](
    func: F[Concatenate[ChoreomapCompiler, T, P], R],
    self: ChoreomapCompiler,
    inst: T,
    *args: P.args,
    **kwargs: P.kwargs
) -> R:
    # TODO: i would like this to be a static method but pyright disagrees
    self.context.push_stack(inst)
    output = func(self, inst, *args, **kwargs)
    self.context.pop_stack()
    return output

class ChoreomapCompiler:
    def __init__(self):
        self.context: StreamContext = StreamContext(Scope.empty())
        self.streams: list[StreamContext] = [self.context]
        self.analysis: Analysis = Analysis(())
        #self.externals: dict[str, ExternalObject] = {}
        self.match_value: TaggedValue = Tag.NONE, 0 # output of latest match statement
        self.string_cache: dict[str, int] = {}
    
    def add_event(self, event: BaseEvent) -> None:
        self.context.add_event(event)
    
    @contextmanager
    def match(self, value: Value):
        simple = isinstance(value, (Tag, int))
        
        matching = False
        possible_tags = {value} if simple else {tag for tag in Tag} # TODO: better analysis of what tags are possible
        matched_tags = set[Tag]()
        
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
            
            matching = True
            old_context = self.context
            self.context = self.context if matched_tags else DummyContext(self.context)
            
            if not simple and matched_tags:
                conditions = [value == tag for tag in matched_tags]
                condition = conditions[0] if len(conditions) == 1 else OrCondition(tuple(conditions))
                with self.context.if_condition(condition):
                    yield
            else:
                yield
            
            self.context = old_context
            matching = False
        
        if simple:
            yield case
        else:
            self.context.use_dynamic_timing()
            tag_index, value_index = self.context.allocate_temp()
            yield case
            self.match_value = (ArrayValue(None, tag_index), ArrayValue(None, value_index))
        
        unmatched_tags = possible_tags - matched_tags
        if unmatched_tags:
            raise ValueError(f'The following tags were not matched: {', '.join(str(tag) for tag in unmatched_tags)}')
    
    def match_return(self, tag: Value, value: Value):
        if not isinstance(self.context, DummyContext):
            self.match_value = tag, value
    
    def allocate(self, *values: Value) -> Value:
        ref = VariableValue('$REF')
        name = NumberString(ref)
        # increment the heap counter
        self.add_event(SetVariableEvent('$REF', ref + 1))
        # copy in each value
        for i, value in enumerate(values):
            self.add_event(SetArrayEvent(name, index=i, value=value))
        return ref
    
    def allocate_to_temp(self, *values: Value) -> TaggedValue:
        ref = self.allocate(*values)
        tag_index, value_index = self.context.allocate_temp()
        self.add_event(SetArrayEvent(None, tag_index, Tag.NONE))
        self.add_event(SetArrayEvent(None, value_index, ref))
        return Tag.NONE, ArrayValue(None, value_index)
    
    def allocate_string(self, string: String) -> TaggedValue:
        if isinstance(string, str):
            if string not in self.string_cache:
                self.string_cache[string] = len(self.string_cache) + 1
                self.streams[0].add_event(SetArrayStringEvent(NumberString(self.string_cache[string]), string))
            ref = self.string_cache[string]
        else:
            ref = self.allocate()
            self.add_event(SetArrayStringEvent(NumberString(ref), string))
        
        tag_index, value_index = self.context.allocate_temp()
        self.add_event(SetArrayEvent(None, tag_index, Tag.STRING))
        self.add_event(SetArrayEvent(None, value_index, ref))
        return Tag.STRING, ArrayValue(None, value_index)
    
    def allocate_array(self, *tagged_values: TaggedValue) -> TaggedValue:
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
    
    def raise_exception(self, message: String):
        tag, value = self.allocate_string(message)
        if self.context is self.streams[1]: # TODO: better way to tell if we're in main stream?
            self.context.unhandled_exception(tag, value)
        else:
            self.context.return_value(tag, value, exception=True)
    
    @contextmanager
    def new_scope(self, is_async: bool) -> Generator[int]:
        # store old context and make new one
        old_context = self.context
        scope = self.analysis.scopes[len(self.streams) - 1]
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
            with context.if_condition(VariableValue('$_') == 0) as elseif:
                _, async_pointer = self.allocate_to_temp(0, Tag.NONE, 0, 0)
                elseif() # if the discard flag is set to true, we create a detached coroutine
                self.add_event(SetArrayEvent(None, async_pointer, 0))
            self.context.make_async(async_pointer)
        
        # execute inner code
        yield len(self.streams) # id of stream
        
        if self.context is not context:
            raise ValueError('Scope nesting invariant was violated. This should only happen if scopes are being created manually.')
        
        # finalize stream and restore old values
        if context is not self.streams[1]: # TODO: better way to check if we're in main stream
            context.return_value(Tag.NONE, 0)
        self.context = old_context
    
    def compile(self, script: Script):
        analysis = ChoreomapAnalyzer().analyze(script)
        self.analysis = analysis
        
        main_id = len(self.streams) # should be 1
        module_id = self.visit_stream(script.instructions, is_async=False)
        
        self.add_event(SetVariableEvent('$REF', len(self.string_cache)))
        self.add_event(StartStreamEvent(module_id, ref_id=0, immediate=True, locals=()))
        
        # TODO: actually set the properties properly
        streams = tuple(Stream(i + 1, tuple(stream.events)) for i, stream in enumerate(self.streams))
        return Choreomap(
            streams=streams,
            input_rating_definitions=(),
            main_id=main_id
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
                obj = self.visit_expr(node, discard=True)
                if isinstance(obj, ExternalObject):
                    self.discard_builtin(obj)
            
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
                self.context.use_dynamic_timing()
                condition = self.visit_condition(condition)
                
                yes_index = self.context.add_placeholder()
                
                for inst in yes:
                    self.visit_inst(inst)
                
                no_index = self.context.add_placeholder()
                
                for inst in no:
                    self.visit_inst(inst)
                
                end_index = len(self.context)
                self.context.replace_event(yes_index, IfEvent(condition, None, JumpEvent(no_index + 1)))
                self.context.replace_event(no_index, JumpEvent(end_index))
            
            case WhileInstruction(condition, body):
                self.context.use_dynamic_timing()
                start_index = len(self.context)
                condition = self.visit_condition(condition)
                with self.context.loop(condition, start_index):
                    for inst in body:
                        self.visit_inst(inst)
            
            case BreakInstruction(should_continue):
                self.context.break_loop(should_continue)
            
            case ReturnInstruction(expr, exception):
                tag, value = self.visit_value(expr)
                self.context.return_value(tag, value, exception)
            
            case _:
                raise NotImplementedError(f'Unsupported instruction: {type(node)}')
    
    @push_stack
    def visit_expr(self, node: BaseExpression, discard: bool = False) -> CompilerObject:
        match node:
            case NumberExpression(value):
                return Tag.NUMBER, value
            
            case BooleanExpression(value):
                return Tag.NUMBER, value
            
            case StringExpression(value):
                return value
            
            case FunctionExpression(args, instructions, is_async):
                stream_id = self.visit_stream(instructions, is_async)
                scope = self.analysis.scopes[stream_id - 2] # stream id is 1-indexed, and the first stream is reserved
                
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
                        return ExternalObject(name)
                
                return tag, value
            
            case LogicalExpression(conjunctive, conditions):
                #conditions = tuple(self.visit_condition(condition) for condition in conditions)
                #return Tag.NUMBER, AndCondition(conditions)
                
                tag1, value1 = self.visit_value(conditions[0])
                if len(conditions) == 1:
                    # in case a degenerate AND is created - shouldn't happen with normal usage
                    return tag1, value1
                
                # store the outputted value in a temporary slot
                tag, value = self.context.allocate_temp()
                
                # we do control flow so we can short circuit on the first truthy/falsy value
                with self.context.if_condition(self.cast_to_condition((tag1, value1)), flip=conjunctive) as elseif:
                    self.add_event(SetArrayEvent(None, tag, tag1))
                    self.add_event(SetArrayEvent(None, value, value1))
                    
                    for i, condition in enumerate(conditions[1:]):
                        tagi, valuei = self.visit_value(condition)
                        condition = self.cast_to_condition((tagi, valuei)) if i < len(conditions) - 1 else None
                        elseif(condition)
                        
                        self.add_event(SetArrayEvent(None, tag, tagi))
                        self.add_event(SetArrayEvent(None, value, valuei))
                
                return tag, value
            
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
                self.context.use_dynamic_timing()
                tag_index, value_index = self.context.allocate_temp()
                
                yes_index = self.context.add_placeholder()
                
                ytag, yes = self.visit_value(yes)
                self.add_event(SetArrayEvent(None, tag_index, ytag))
                self.add_event(SetArrayEvent(None, value_index, yes))
                
                no_index = self.context.add_placeholder()
                
                ntag, no = self.visit_value(no)
                self.add_event(SetArrayEvent(None, tag_index, ntag))
                self.add_event(SetArrayEvent(None, value_index, no))
                
                # TODO: we can do these jumps simpler i think
                end_index = len(self.context)
                condition = self.visit_condition(condition)
                self.context.replace_event(yes_index, IfEvent(condition, None, JumpEvent(no_index + 1)))
                self.context.replace_event(no_index, JumpEvent(end_index))
                
                return ArrayValue(None, tag_index), ArrayValue(None, value_index)
            
            case CallExpression(func, args):
                obj = self.visit_expr(func)
                
                if isinstance(obj, ExternalObject):
                    return self.call_builtin(obj, *args)
                
                # TODO: verify tag
                _, ref = self.cast_to_value(obj)
                
                # copy arguments into register for callee function
                for i, arg in enumerate(args):
                    tag, value = self.visit_value(arg)
                    self.add_event(SetArrayEvent('$ARGS', 2 * i, tag))
                    self.add_event(SetArrayEvent('$ARGS', 2 * i + 1, value))
                
                # set the environment pointer so the function can load the closure
                self.add_event(SetVariableEvent('$ENV', ref))
                
                # set the discard flag so coroutines know if they're detached
                self.add_event(SetVariableEvent('$_', int(discard)))
                
                # synchronous functions don't need a ref_id because they finish instantly
                # TODO: but we call coroutines here too, hmm...
                stream_id = self.deref(ref, 0)
                self.add_event(StartStreamEvent(stream_id, 0, immediate=True))
                
                self.context.throw_if(
                    VariableValue('$EXC') != 0,
                    VariableValue('$RTAG'),
                    VariableValue('$RETURN')
                ) # TODO: this can be optimised when the stream is synchronous -- we're copying $RTAG/$RETURN to themselves
                
                tag_index, value_index = 0, 0
                if not discard:
                    tag_index, value_index = self.context.allocate_temp()
                    self.add_event(SetArrayEvent(None, tag_index, VariableValue('$RTAG')))
                    self.add_event(SetArrayEvent(None, value_index, VariableValue('$RETURN')))
                return ArrayValue(None, tag_index), ArrayValue(None, value_index)
            
            case JoinExpression(strings):
                # TODO: verify tag
                strings = tuple(self.visit_str(string) for string in strings)
                return JoinString(strings)
            
            case CompareExpression(first, operands, operators):
                # TODO: verify tags
                _, first = self.visit_value(first)
                operands = tuple(self.visit_value(operand)[1] for operand in operands)
                assert 0 < len(operands)
                assert len(operands) == len(operators)
                
                if len(operators) == 1:
                    return CompareCondition(first, operands[0], operators[0])
                else:
                    conditions = tuple(
                        CompareCondition(first if i == 0 else operands[i - 1], operands[i], operators[i])
                        for i in range(len(operators))
                    )
                    return AndCondition(conditions)
            
            case AwaitExpression(expr):
                if not self.context.is_async:
                    raise ValueError('Await expression encountered in synchronous context.')
                
                obj = self.visit_expr(expr)
                if isinstance(obj, ExternalCoroutine):
                    return self.await_builtin(obj)
                
                tag, value = self.cast_to_value(obj)
                with self.match(tag) as case:
                    with case(Tag.COROUTINE):
                        finished = self.deref(value, 0)
                        rtag = self.deref(value, 1)
                        rval = self.deref(value, 2)
                        t = self.deref(value, 3)
                        self.add_event(WaitEvent(finished != 0))
                        self.context.wait(t) # update local timekeeping
                        self.context.throw_if(finished < 0, rtag, rval)
                        
                        self.match_return(rtag, rval)
                    
                    with case():
                        self.match_return(tag, value) # TODO: throw error
                
                return self.match_value
            
            case ListExpression(exprs):
                return [self.visit_value(expr) for expr in exprs]
            
            case NullExpression():
                return None
            
            case _:
                raise NotImplementedError(f'Unsupported expression: {type(node).__name__}')
    
    
    def cast_to_value(self, obj: CompilerObject) -> TaggedValue:
        match obj:
            case tuple((tag, value)):
                return tag, value
            case BaseCondition() | bool():
                return Tag.NUMBER, IfValue(obj, 1, 0)
            case BaseString() | str():
                return self.allocate_string(obj)
            case list():
                _, ref = self.allocate_array(*(self.cast_to_value(elm) for elm in obj))
                return Tag.ARRAY, ref
            case None:
                return Tag.NONE, 0
            case ExternalObject(name):
                raise ValueError(f'Cannot convert builtin "{name}" to value.')
    
    def visit_value(self, node: BaseExpression) -> TaggedValue:
        obj = self.visit_expr(node)
        return self.cast_to_value(obj)
    
    def cast_to_condition(self, obj: CompilerObject) -> Condition:
        match obj:
            case (_, float()) | (_, int()) | bool() | str() | list() | None:
                return bool(obj) # TODO: this is incorrect for _, float() and _, int()
            
            case BaseValue() | float() | int() as tag, BaseValue() | float() | int() as value:
                mapping = {
                    Tag.NONE: False,
                    Tag.NUMBER: value != 0,
                    Tag.STRING: ArrayValue(NumberString(value)) != 0,
                    Tag.FUNCTION: True,
                    Tag.COROUTINE: True,
                    Tag.ARRAY: ArrayValue(NumberString(value)) != 0,
                    Tag.OBJECT: True,
                }
                
                if isinstance(tag, Tag):
                    return mapping.get(tag, False)
                else:
                    conditions = tuple(
                        tag == t
                        if mapping[t] is True
                        else AndCondition((tag == t, mapping[t])) # can't use & because both sides could be bool
                        for t in Tag if mapping[t] is not False
                    )
                    return OrCondition(conditions)
            
            case BaseCondition():
                return obj
            
            case BaseString():
                _, ref = self.allocate_string(obj)
                return ArrayValue(NumberString(ref)) != 0
            
            case ExternalObject(name):
                raise ValueError(f'Cannot convert builtin "{name}" to condition.')
    
    
    def visit_condition(self, node: BaseExpression) -> Condition:
        obj = self.visit_expr(node)
        return self.cast_to_condition(obj)
    
    
    def visit_str(self, node: BaseExpression) -> String:
        obj = self.visit_expr(node)
        match obj:
            case (_, float()) | (_, int()) | bool() | str() | list() | None:
                return str(obj) # TODO: this is incorrect for (_, float()) and (_, int())
            
            case tag, BaseValue() as value:
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
                    return mapping[tag]
                else:
                    return reduce(
                        lambda acc, t: IfString(tag == t, mapping[t], acc),
                        Tag,
                        '<unknown>'
                    )
            
            case BaseCondition():
                return IfString(obj, 'True', 'False')
            
            case BaseString():
                return obj
            
            case ExternalObject(name):
                raise ValueError(f'Cannot convert builtin "{name}" to string.')
    
    def call_builtin(self, obj: ExternalObject, *args: BaseExpression) -> CompilerObject:
        raise ValueError(f'Unknown builtin {obj.name}.')
    
    def await_builtin(self, obj: ExternalCoroutine) -> CompilerObject:
        raise ValueError(f'Unknown builtin {obj.name}.')
    
    def discard_builtin(self, obj: ExternalObject) -> None:
        if isinstance(obj, ExternalCoroutine):
            raise ValueError(f'Builtin coroutine {obj.name} was never awaited.')
