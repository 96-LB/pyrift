from abc import abstractmethod
from collections.abc import Sequence
from contextlib import contextmanager
from types import TracebackType
from typing import override

from ..backend import BaseEvent, Value
from ..ir import BaseInstruction
from ..vars import Tag
from .base import BaseContext
from .null import NullContext


class CaseContext(BaseContext):
    def __init__(self, context: BaseContext):
        super().__init__()
        self.target_context = context
        self.context: BaseContext | None = None
        self.active_case: tuple[Tag, ...] | None = None
        self.matched_tags = set[Tag]()
        self.entered = False
        self.output: tuple[Value, Value] = (Tag.NONE, 0)
    
    def __enter__(self):
        if self.entered:
            raise ValueError('Match context has already been entered.')
        self.entered = True
        
        return self
    
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        if not exc_val:
            self.ensure_fully_matched()
    
    def ensure_context(self) -> BaseContext:
        if self.context is None:
            raise ValueError('Attempted to use match context without specifying a case.')
        return self.context
    
    @override
    def __len__(self) -> int:
        return len(self.ensure_context())
    
    @property
    @override
    def is_async(self) -> bool:
        return self.ensure_context().is_async
    
    @override
    def add_event(self, event: BaseEvent):
        return self.ensure_context().add_event(event)
    
    @override
    def replace_event(self, index: int, event: BaseEvent):
        return self.ensure_context().replace_event(index, event)
    
    @override
    def lookup(self, name: str):
        return self.ensure_context().lookup(name)
    
    @override
    def allocate_temp(self) -> tuple[int, int]:
        return self.ensure_context().allocate_temp()
    
    @override
    def push_stack(self, instruction: BaseInstruction, index: int):
        return self.ensure_context().push_stack(instruction, index)
    
    @override
    def pop_stack(self):
        return self.ensure_context().pop_stack()
    
    @override
    def get_parent_instruction(self):
        return self.ensure_context().get_parent_instruction()
    
    @override
    def jump_up_stack(self):
        return self.ensure_context().jump_up_stack()
    
    @override
    def wait(self, seconds: Value) -> None:
        return self.ensure_context().wait(seconds)
    
    @override
    def begin_control_flow(self) -> None:
        return self.ensure_context().begin_control_flow()
    
    @abstractmethod
    def match_tags(self, *tags: Tag) -> Sequence[Tag]:
        ...
    
    @abstractmethod
    def ensure_fully_matched(self):
        ...
    
    @contextmanager
    def case(self, *tags: Tag):
        if self.context is not None:
            raise ValueError('Cases cannot be nested.')
        
        matched_tags = self.match_tags(*tags)
        for tag in matched_tags:
            if tag in self.matched_tags:
                raise ValueError(f'Tag {tag} has already been matched.')
            else:
                self.matched_tags.add(tag)
        
        self.context = self.target_context if matched_tags else NullContext()
        yield
        self.context = None
    
    
    @contextmanager
    def default(self):
        tags = tuple(tag for tag in Tag if tag not in self.matched_tags)
        with self.case(*tags):
            yield
