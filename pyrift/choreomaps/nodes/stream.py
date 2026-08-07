from collections.abc import Sequence
from dataclasses import dataclass, fields

from util import snake_to_camel

from .enum import TimingMode
from .event import BaseEvent
from .value import BaseValue, ConstantValue


@dataclass(frozen=True)
class Stream:
    '''
    Attributes:
        id: Unique ID of the stream. Needed for the cancellation of running streams.
        events: List of events in this stream
        timing_mode: Timing mode of this stream. Defaults to SongStart
    '''
    
    id: int
    events: tuple[BaseEvent, ...]
    timing_mode: TimingMode = TimingMode.SONG_START
    
    _vars: tuple[str, ...] = ()
    
    def pad_locals(self, args: Sequence[BaseValue]):
        if len(args) > len(self._vars):
            raise ValueError(f'Too many stream arguments were provided. Expected at most {len(self._vars)}, got {len(args)}.')
        return tuple(args) + (ConstantValue(0),) * (len(self._vars) - len(args))
    
    def to_dict(self):
        field_values = {snake_to_camel(f.name): getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}
        return field_values
