
from pyrift.choreomaps.backend.event import JumpEvent
from pyrift.choreomaps.ir.instruction import BaseInstruction

from .analysis import Scope
from .backend import (
    ArrayValue,
    BaseEvent,
    CompareCondition,
    EventBackend,
    MathValue,
    NumberString,
    SetArrayEvent,
    SetVariableEvent,
    StopStreamEvent,
    SystemValue,
    Value,
    WaitEvent,
)
from .enum import BinaryOperator, ComparisonMode, SystemAttribute
from .vars import Tag


class StreamContext:
    def __init__(self, scope: Scope):
        self.scope: Scope = scope
        self.async_ref: Value | None = None
        self.events: list[EventBackend] = []
        self.temp_index: int = 0
        self.stack: list[tuple[BaseInstruction, int]] = []
        self.t_index: int = 0
        self.t: float = 0
        self.simple: bool = True
    
    def add_event(self, event: BaseEvent):
        self.events.append(EventBackend(self.t, event))
    
    def replace_event(self, index: int, event: BaseEvent):
        self.events[index] = EventBackend(self.events[index].t, event)
    
    def allocate_temp(self) -> tuple[int, int]:
        self.temp_index += 2
        # tag index, value index
        return (self.temp_index - 2, self.temp_index - 1)
    
    def push_stack(self, instruction: BaseInstruction, index: int):
        self.stack.append((instruction, index))
    
    def pop_stack(self):
        return self.stack.pop()
    
    def get_parent_instruction(self):
        return self.stack[-1][0]
    
    def jump_up_stack(self):
        index = self.stack[-1][1]
        return JumpEvent(index)
    
    
    def wait(self, seconds: Value) -> None:
        if self.simple and isinstance(seconds, (int, float)):
            self.t += seconds
        else:
            self.upgrade_timekeeping()
            time = SystemValue(SystemAttribute.STREAM_TIME)
            self.add_event(SetArrayEvent(None, self.t_index, MathValue(time, seconds, BinaryOperator.ADD)))
            self.add_event(WaitEvent(CompareCondition(time, ArrayValue(None, self.t_index), ComparisonMode.GREATER_EQUAL)))
    
    def upgrade_timekeeping(self) -> None:
        if not self.simple:
            return
        
        # save a local variable to keep track of timekeeping from now on
        _, self.t_index = self.allocate_temp()
        self.add_event(SetArrayEvent(None, self.t_index, self.t))
        self.t = 0
        self.simple = False
    
    def make_async(self, async_ref: Value):
        if self.async_ref:
            raise ValueError(f'Stream is already async with ref {self.async_ref}.')
        self.async_ref = async_ref
    
    def return_value(self, tagged_value: tuple[Value, Value] | None = None):
        tag, value = tagged_value or (Tag.NONE, 0)
        
        # async functions need to update their coroutine object
        if self.async_ref:
            ref = NumberString(self.async_ref)
            self.add_event(SetArrayEvent(ref, 0, 1)) # mark as finished
            self.add_event(SetArrayEvent(ref, 1, tag))
            self.add_event(SetArrayEvent(ref, 2, value))
            self.add_event(SetArrayEvent(ref, 3, self.t))
            tag = Tag.COROUTINE
            value = self.async_ref
        
        self.add_event(SetVariableEvent('$RTAG', tag))
        self.add_event(SetVariableEvent('$RETURN', value))
        self.add_event(StopStreamEvent())
