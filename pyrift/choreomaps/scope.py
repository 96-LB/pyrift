
from collections.abc import Sequence
from dataclasses import field

from pyrift.choreomaps.nodes.event import BaseEvent, SetArrayEvent, SetVariableEvent
from pyrift.choreomaps.nodes.stream import Stream

from .nodes import ArrayValue, ConstantValue


class Scope:
    
    def __init__(self, id: int, args: Sequence[str]):
        self.id: int = id
        self.argc: int = len(args)
        self.vars: list[str] = list(args)
        self.events: list[BaseEvent] = field(default_factory=list[BaseEvent])
        self.tempc: int = 0
    
    def get(self, name: str):
        return self.vars.index(name) if name in self.vars else None
    
    def set(self, name: str):
        self.vars.append(name)
    
    def temp(self):
        self.set(f"$T{self.tempc}")
        self.tempc += 1
        return len(self.vars) - 1
    
    def list_vars(self):
        return tuple(self.vars)
    
    def get_locals(self):
        return tuple(ArrayValue(index=ConstantValue(i)) for i in range(len(self.vars)))
    
    def load_locals(self):
        return (
            SetArrayEvent(0, index=ConstantValue(i), value=ArrayValue("$ARGS", index=ConstantValue(i)))
            for i in range(self.argc)
        )
    
    def to_stream(self):
        events = (
            SetArrayEvent(0, value=ConstantValue(len(self.vars))), # set the locals array length
            *self.load_locals(), # copy locals from global args register
            SetVariableEvent(0, "$RETURN", ConstantValue(0)),
            *self.events,
        )
        return Stream(id=self.id, events=events, _vars=tuple(self.vars))
