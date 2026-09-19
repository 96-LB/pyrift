from pyrift.jobj import JList, JObj

from ..enum import TimingMode
from .event import TimedEvent


class Stream(JObj):
    '''
    Attributes:
        id: Unique ID of the stream. Needed for the cancellation of running streams.
        events: List of events in this stream
        timing_mode: Timing mode of this stream. Defaults to StreamStart
    '''
    
    id: int
    events: JList[TimedEvent]
    timing_mode: TimingMode = TimingMode.STREAM_START
