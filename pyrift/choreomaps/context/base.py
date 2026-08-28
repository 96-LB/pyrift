from abc import ABC, abstractmethod

from ..backend import BaseEvent, Value
from ..ir import BaseInstruction
from ..vars import VarType


class BaseContext(ABC):
    @abstractmethod
    def __len__(self) -> int:
        ...
    
    @property
    @abstractmethod
    def is_async(self) -> bool:
        ...
    
    @abstractmethod
    def add_event(self, event: BaseEvent):
        ...
    
    @abstractmethod
    def replace_event(self, index: int, event: BaseEvent):
        ...
    
    @abstractmethod
    def lookup(self, name: str) -> tuple[int, VarType]:
        ...
    
    @abstractmethod
    def allocate_temp(self) -> tuple[int, int]:
        ...
    
    @abstractmethod
    def push_stack(self, instruction: BaseInstruction) -> None:
        ...
    
    @abstractmethod
    def pop_stack(self) -> BaseInstruction:
        ...
    
    @abstractmethod
    def get_parent_instruction(self) -> type[BaseInstruction]:
        ...
    
    @abstractmethod
    def wait(self, seconds: Value) -> None:
        ...
    
    @abstractmethod
    def begin_control_flow(self) -> None:
        ...
    
    @abstractmethod
    def return_value(self, tag: Value, value: Value) -> None:
        ...
