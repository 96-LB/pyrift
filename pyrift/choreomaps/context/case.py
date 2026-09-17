from abc import abstractmethod
from collections.abc import Sequence
from contextlib import contextmanager
from types import TracebackType
from typing import override

from ..backend import BaseEvent, Value
from ..vars import Tag
from .base import BaseContext, ContextStatus


class CaseContext(BaseContext):
    def __init__(self, context: BaseContext):
        super().__init__(context)
        self.matched_tags = set[Tag]()
        self.output: tuple[Value, Value] = (Tag.NONE, 0)
        self.is_branch_active: bool | None = None # bool = whether current branch matched, None = no branch
    
    @override
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        if exc_val is None:
            self.ensure_fully_matched()
    
    @override
    def add_event(self, event: BaseEvent):
        if self.is_branch_active is None:
            raise ValueError('Attempted to use case context without specifying a case.')
        elif self.is_branch_active:
            return super().add_event(event)
    
    @override
    def replace_event(self, index: int, event: BaseEvent):
        if self.is_branch_active is None:
            raise ValueError('Attempted to use case context without specifying a case.')
        elif self.is_branch_active:
            return super().replace_event(index, event)
    
    @abstractmethod
    def match_tags(self, *tags: Tag) -> Sequence[Tag]:
        ...
    
    @abstractmethod
    def ensure_fully_matched(self):
        ...
    
    @abstractmethod
    def set_output(self, tag: Value, value: Value) -> None:
        ...
    
    @contextmanager
    def case(self, *tags: Tag):
        if self.status is not ContextStatus.ACTIVE:
            raise ValueError('Cases can only be matched within a match context.')
        if self.is_branch_active is not None:
            raise ValueError('Cases cannot be nested.')
        
        matched_tags = self.match_tags(*tags)
        for tag in matched_tags:
            if tag in self.matched_tags:
                raise ValueError(f'Tag {tag} has already been matched.')
            else:
                self.matched_tags.add(tag)
        
        self.is_branch_active = len(matched_tags) > 0
        yield
        self.is_branch_active = None
    
    
    @contextmanager
    def default(self):
        tags = tuple(tag for tag in Tag if tag not in self.matched_tags)
        with self.case(*tags):
            yield
