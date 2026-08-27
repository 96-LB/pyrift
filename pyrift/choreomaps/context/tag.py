from typing import override

from ..backend import Value
from ..vars import Tag
from .base import BaseContext
from .case import CaseContext


class TagContext(CaseContext):
    def __init__(self, context: BaseContext, tag: Tag):
        super().__init__(context)
        self.tag = tag
    
    @override
    def return_value(self, tag: Value, value: Value) -> None:
        if self.ensure_context() is self.target_context:
            self.output = (tag, value)
    
    @override
    def ensure_fully_matched(self) -> None:
        if self.tag not in self.matched_tags:
            raise ValueError(f'The tag {self.tag} was not matched.')
    
    @override
    def match_tags(self, *tags: Tag) -> tuple[Tag] | tuple[()]:
        if self.tag not in tags:
            return ()
        return (self.tag,)
