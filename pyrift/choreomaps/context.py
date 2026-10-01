from contextlib import contextmanager

from .analysis import Scope
from .backend import (
    ArrayValue,
    BaseEvent,
    Condition,
    FinishLevelEvent,
    IfEvent,
    JumpEvent,
    LogEvent,
    NumberString,
    SetArrayEvent,
    SetVariableEvent,
    StopStreamEvent,
    SystemValue,
    TimedEvent,
    Value,
    WaitEvent,
)
from .enum import SystemAttribute
from .ir import BaseInstruction
from .vars import Tag, VarType


class StreamContext:
    def __init__(self, scope: Scope):
        self.scope: Scope = scope
        self.async_ref: Value | None = None
        self.events: list[TimedEvent] = []
        self.temp_index: int = 0
        self.stack: list[BaseInstruction] = []
        self.t_index: int = 0
        self.t: float = 0
        self.discard_index: int = 0
        self.simple: bool = True
        self.has_waited: bool = False
        self.loops: list[list[int]] = [] # each entry is a start index followed by breakpoints
    
    
    def __len__(self) -> int:
        return len(self.events)
    
    
    @property
    def is_async(self) -> bool:
        return self.async_ref is not None
    
    
    def add_event(self, event: BaseEvent) -> int:
        self.events.append(TimedEvent(self.t, event))
        return len(self.events) - 1
    
    
    def add_placeholder(self) -> int:
        return self.add_event(BaseEvent())
    
    
    def replace_event(self, index: int, event: BaseEvent) -> None:
        self.events[index] = TimedEvent(self.events[index].t, event)
    
    
    def lookup(self, name: str) -> tuple[int, VarType]:
        index = 0
        for i in range(len(self.scope.vars)):
            var_type = self.scope.types[i]
            if self.scope.vars[i] == name:
                return index, var_type
            if var_type in (VarType.LOCAL, VarType.CAPTURED, VarType.NONLOCAL):
                index += 2
        raise ValueError(f'Unknown variable {name}.')
    
    
    def allocate_temp(self) -> tuple[int, int]:
        self.temp_index += 2
        # tag index, value index
        return (self.temp_index - 2, self.temp_index - 1)
    
    
    def push_stack(self, instruction: BaseInstruction) -> None:
        self.stack.append(instruction)
    
    
    def pop_stack(self) -> BaseInstruction:
        return self.stack.pop()
    
    
    def get_parent_instruction(self) -> type[BaseInstruction]:
        return type(self.stack[-2])
    
    
    def wait(self, seconds: Value) -> None:
        self.ensure_async_output()
        
        if self.simple and isinstance(seconds, (int, float)):
            self.t += seconds
        else:
            self.use_dynamic_timing()
            t = ArrayValue(None, self.t_index)
            self.add_event(SetArrayEvent(None, self.t_index, t + seconds))
            self.add_event(WaitEvent(SystemValue(SystemAttribute.STREAM_TIME) >= t))
    
    
    def use_dynamic_timing(self) -> None:
        if not self.simple or not self.is_async:
            return
        
        # save a local variable to keep track of timekeeping from now on
        _, self.t_index = self.allocate_temp()
        self.add_event(SetArrayEvent(None, self.t_index, self.t))
        self.t = 0
        self.simple = False
    
    
    def make_async(self, async_ref: Value):
        if self.is_async:
            raise ValueError(f'Stream is already async with ref {self.async_ref}.')
        self.async_ref = async_ref
    
    
    def ensure_async_output(self):
        if self.async_ref is None:
            raise ValueError('Attempted to use async operation in a synchronous stream.')
        
        if not self.has_waited:
            self.add_event(SetVariableEvent('$RTAG', Tag.COROUTINE))
            self.add_event(SetVariableEvent('$RETURN', self.async_ref))
            self.add_event(SetVariableEvent('$EXC', 0))
            self.has_waited = True
    
    
    def unhandled_exception(self):
        self.add_event(LogEvent('<color=#ffff00>An unhandled error has occurred.'))
        self.add_event(FinishLevelEvent(False))
    
    
    def return_value(self, tag: Value, value: Value, exception: bool = False) -> None:
        # async functions need to update their coroutine object
        if self.async_ref is not None:
            with self.if_condition(self.async_ref != 0) as elseif:
                ref = NumberString(self.async_ref)
                status = -1 if exception else 1 # negative numbers mean failure
                self.add_event(SetArrayEvent(ref, 0, status)) # mark as finished
                self.add_event(SetArrayEvent(ref, 1, tag))
                self.add_event(SetArrayEvent(ref, 2, value))
                self.add_event(SetArrayEvent(ref, 3, self.t))
                self.ensure_async_output()
                
                if exception:
                    elseif()
                    self.unhandled_exception()
        else:
            self.add_event(SetVariableEvent('$RTAG', tag))
            self.add_event(SetVariableEvent('$RETURN', value))
            self.add_event(SetVariableEvent('$EXC', exception))
        self.add_event(StopStreamEvent())
    
    
    @contextmanager
    def if_condition(self, condition: Condition, use_dynamic_timing: bool = False):
        if isinstance(condition, bool):
            raise ValueError('Compiler can evaluate compile-time condition as a boolean—this is probably a mistake.')
        
        if use_dynamic_timing:
            self.use_dynamic_timing()
        
        condition_index = self.add_placeholder()
        end_indices = list[int]()
        elsed = False
        
        def elseif(else_condition: Condition | None = None):
            nonlocal elsed, condition, condition_index
            
            if elsed:
                raise ValueError('Cannot use elseif after using else in dynamic if statement.')
            
            end_indices.append(self.add_placeholder())
            self.replace_event(condition_index, IfEvent(condition, yes=None, no=JumpEvent(len(self))))
            
            if else_condition:
                condition = else_condition
                condition_index = self.add_placeholder()
            else:
                elsed = True
        
        yield elseif
        
        for end_index in end_indices:
            self.replace_event(end_index, JumpEvent(len(self)))
        
        if not elsed:
            self.replace_event(condition_index, IfEvent(condition, yes=None, no=JumpEvent(len(self))))
    
    
    def throw_if(self, condition: Condition, tag: Value, value: Value):
        with self.if_condition(condition):
            self.return_value(tag, value, exception=True)
    
    
    @contextmanager
    def loop(self, condition: Condition, start_index: int):
        self.loops.append([start_index])
        self.use_dynamic_timing()
        
        jump_index = self.add_placeholder()
        yield
        self.add_event(JumpEvent(start_index))
        end = JumpEvent(len(self))
        self.replace_event(jump_index, IfEvent(condition, None, end))
        for breakpoint in self.loops.pop()[1:]:
            self.replace_event(breakpoint, end)
    
    
    def break_loop(self, should_continue: bool):
        if not self.loops:
            raise ValueError(f'"{'continue' if should_continue else 'break'}" can only be used inside a loop.')
        
        if should_continue:
            self.add_event(JumpEvent(self.loops[-1][0])) # jump to start
        else:
            self.loops[-1].append(len(self))
            self.add_placeholder()


class DummyContext(StreamContext):
    def __init__(self, parent: StreamContext | None = None):
        super().__init__(Scope((), (), 0))
        if parent:
            self.async_ref = parent.async_ref
