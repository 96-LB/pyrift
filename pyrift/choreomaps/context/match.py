from types import TracebackType
from typing import override

from ..backend import (
    AndCondition,
    ArrayValue,
    CompareCondition,
    Condition,
    IfEvent,
    JumpEvent,
    SetArrayEvent,
    Value,
)
from ..enum import ComparisonMode
from ..vars import Tag
from .base import BaseContext, BaseEvent
from .case import CaseContext


class MatchContext(CaseContext):
    def __init__(self, context: BaseContext, value: Value):
        super().__init__(context)
        self.value = value
        self.possible_tags = {tag for tag in Tag if self.is_tag_possible(tag)}
        self.tag_index = 0
        self.value_index = 0
        self.jumps: list[tuple[int, Condition]] = []
    
    @override
    def __enter__(self):
        super().__enter__()
        self.parent.begin_control_flow()
        self.tag_index, self.value_index = self.parent.allocate_temp()
        self.output = (ArrayValue(None, self.tag_index), ArrayValue(None, self.value_index))
        return self
    
    @override
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        super().__exit__(exc_type, exc_val, exc_tb)
        for i, (index, condition) in enumerate(self.jumps):
            jump_index = self.jumps[i + 1][0] if i + 1 < len(self.jumps) else len(self.parent)
            self.parent.replace_event(index, IfEvent(condition, JumpEvent(jump_index), None))
    
    @override
    def ensure_fully_matched(self) -> None:
        unmatched_tags = self.possible_tags - self.matched_tags
        if unmatched_tags:
            raise ValueError(f'The following tags were not matched: {', '.join(str(tag) for tag in unmatched_tags)}')
    
    @override
    def match_tags(self, *tags: Tag) -> list[Tag]:
        matched_tags: list[Tag] = []
        for tag in tags:
            if tag in self.possible_tags:
                matched_tags.append(tag)
        
        if matched_tags:
            # add a jump instruction if this branch succeeded
            conditions = [CompareCondition(self.value, tag, ComparisonMode.NOT_EQUAL) for tag in matched_tags]
            condition = conditions[0] if len(conditions) == 1 else AndCondition(tuple(conditions))
            self.jumps.append((len(self.parent), condition))
            self.parent.add_event(BaseEvent()) # placeholder jump
        return matched_tags
    
    @override
    def set_output(self, tag: Value, value: Value) -> None:
        self.add_event(SetArrayEvent(None, self.tag_index, tag))
        self.add_event(SetArrayEvent(None, self.value_index, value))
    
    def is_tag_possible(self, tag: Tag):
        if not isinstance(self.value, (Tag, int)):
            return True
        return self.value == tag