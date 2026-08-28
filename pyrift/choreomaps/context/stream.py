from typing import override

from ..analysis import Scope
from ..backend import (
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
from ..enum import BinaryOperator, ComparisonMode, SystemAttribute
from ..ir import BaseInstruction
from ..vars import Tag, VarType
from .base import BaseContext


class StreamContext(BaseContext):
    def __init__(self, scope: Scope):
        self.scope: Scope = scope
        self.async_ref: Value | None = None
        self.events: list[EventBackend] = []
        self.temp_index: int = 0
        self.stack: list[BaseInstruction] = []
        self.t_index: int = 0
        self.t: float = 0
        self.simple: bool = True
    
    @override
    def __len__(self) -> int:
        return len(self.events)
    
    @property
    @override
    def is_async(self) -> bool:
        return self.async_ref is not None
    
    @override
    def add_event(self, event: BaseEvent):
        self.events.append(EventBackend(self.t, event))
    
    @override
    def replace_event(self, index: int, event: BaseEvent):
        self.events[index] = EventBackend(self.events[index].t, event)
    
    @override
    def lookup(self, name: str) -> tuple[int, VarType]:
        index = 0
        for i in range(len(self.scope.vars)):
            var_type = self.scope.types[i]
            if self.scope.vars[i] == name:
                return index, var_type
            if var_type in (VarType.LOCAL, VarType.CAPTURED, VarType.NONLOCAL):
                index += 2
        raise ValueError(f'Unknown variable {name}.')
    
    @override
    def allocate_temp(self) -> tuple[int, int]:
        self.temp_index += 2
        # tag index, value index
        return (self.temp_index - 2, self.temp_index - 1)
    
    @override
    def push_stack(self, instruction: BaseInstruction) -> None:
        self.stack.append(instruction)
    
    @override
    def pop_stack(self) -> BaseInstruction:
        return self.stack.pop()
    
    @override
    def get_parent_instruction(self) -> type[BaseInstruction]:
        return type(self.stack[-2])
    
    @override
    def wait(self, seconds: Value) -> None:
        if self.simple and isinstance(seconds, (int, float)):
            self.t += seconds
        else:
            self.begin_control_flow()
            t = ArrayValue(None, self.t_index)
            self.add_event(SetArrayEvent(None, self.t_index, MathValue(t, seconds, BinaryOperator.ADD)))
            self.add_event(WaitEvent(CompareCondition( SystemValue(SystemAttribute.STREAM_TIME), t, ComparisonMode.GREATER_EQUAL)))
    
    @override
    def begin_control_flow(self) -> None:
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
        self.add_event(SetVariableEvent('$RTAG', Tag.COROUTINE))
        self.add_event(SetVariableEvent('$RETURN', async_ref))
    
    def return_value(self, tag: Value, value: Value) -> None:
        # async functions need to update their coroutine object
        if self.async_ref:
            ref = NumberString(self.async_ref)
            self.add_event(SetArrayEvent(ref, 0, 1)) # mark as finished
            self.add_event(SetArrayEvent(ref, 1, tag))
            self.add_event(SetArrayEvent(ref, 2, value))
            self.add_event(SetArrayEvent(ref, 3, self.t))
            tag = Tag.COROUTINE
            value = self.async_ref
        else:
            self.add_event(SetVariableEvent('$RTAG', tag))
            self.add_event(SetVariableEvent('$RETURN', value))
        self.add_event(StopStreamEvent())
