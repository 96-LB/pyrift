from collections.abc import Sequence

from pyrift.jobj import JList, JObj

from ..enum import TimingMode
from .event import BaseEvent
from .value import BaseValue, ConstantValue


class Stream(JObj):
    '''
    Attributes:
        id: Unique ID of the stream. Needed for the cancellation of running streams.
        events: List of events in this stream
        timing_mode: Timing mode of this stream. Defaults to SongStart
    '''
    
    id: int
    events: JList[BaseEvent]
    timing_mode: TimingMode = TimingMode.SONG_START
    
    _vars: JList[str] = ()
    
    def pad_locals(self, args: Sequence[BaseValue]):
        if len(args) > len(self._vars):
            raise ValueError(f'Too many stream arguments were provided. Expected at most {len(self._vars)}, got {len(args)}.')
        return tuple(args) + (ConstantValue(0),) * (len(self._vars) - len(args))
