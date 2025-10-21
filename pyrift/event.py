from dataclasses import dataclass

from .typeddicts import EventDict, EventDataPairDict

from typing import Literal


class DataPairs:
    # TODO: actually implement this class to basically be a multidict
    def to_list(self) -> list[EventDataPairDict]:
        return []


@dataclass
class Event:
    data_pairs: DataPairs
    end_beat: float
    start_beat: float
    track: Literal[1, 2, 3]
    type: str

    def to_dict(self) -> EventDict:
        return {
            'clipin': 0,
            'dataPairs': self.data_pairs.to_list(),
            'endBeatNumber': self.end_beat,
            'group': 0,
            'startBeatNumber': self.start_beat,
            'track': self.track,
            'type': self.type
        }
