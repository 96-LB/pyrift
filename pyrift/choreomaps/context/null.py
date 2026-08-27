from typing import override

from ..backend import BaseEvent, Value
from ..ir import BaseInstruction
from ..vars import VarType
from .base import BaseContext


class NullContext(BaseContext):
    @override
    def __len__(self):
        return 0
    
    @property
    @override
    def is_async(self) -> bool:
        return False
    
    @override
    def add_event(self, event: BaseEvent):
        pass
    
    @override
    def replace_event(self, index: int, event: BaseEvent):
        pass
    
    @override
    def allocate_temp(self) -> tuple[int, int]:
        return (0, 0)
    
    @override
    def lookup(self, name: str) -> tuple[int, VarType]:
        return (0, VarType.EXTERNAL)
    
    @override
    def push_stack(self, instruction: BaseInstruction, index: int) -> None:
        pass
    
    @override
    def pop_stack(self) -> tuple[BaseInstruction, int]:
        return (BaseInstruction(), 0)
    
    @override
    def get_parent_instruction(self) -> BaseInstruction:
        return BaseInstruction()
    
    @override
    def jump_up_stack(self) -> None:
        pass
    
    @override
    def wait(self, seconds: Value) -> None:
        pass
    
    @override
    def begin_control_flow(self) -> None:
        pass
    
    @override
    def return_value(self, tag: Value, value: Value) -> None:
        pass
