from dataclasses import dataclass

from .datapairs import DataPairs
from typeddicts import EventDict

from typing import Any, ClassVar, Literal, Self, Type, TypeGuard, cast



# TODO: move to typing utils file
def is_list[T](obj: Any, type: type[T]) -> TypeGuard[list[T]]:
    if not isinstance(obj, list):
        return False
    return all(isinstance(item, type) for item in cast(list[Any], obj))



@dataclass
class Event:
    subclasses: ClassVar[dict[str, Type[Self]]] = {}
    
    data_pairs: DataPairs
    end_beat: float
    start_beat: float
    track: Literal[1, 2, 3]
    type: str
    
    def __init_subclass__(cls, type: str):
        super().__init_subclass__()
        cls.subclasses[type] = cls
    
    
    @classmethod
    def parse(cls, data: dict[str, object]) -> Self:
        type = data.get('type')
        if not isinstance(type, str):
            type = ''
        
        subclass = cls.subclasses.get(type)
        if subclass is not None:
            return subclass.parse(data)
        
        raw_pairs = data.get('dataPairs')
        if not is_list(raw_pairs, object):
            raw_pairs = []
        data_pairs = DataPairs.parse(raw_pairs)
        # TODO: type utils?
        end_beat = data.get('endBeatNumber')
        if not isinstance(end_beat, (int, float)):
            end_beat = 0
        start_beat = data.get('startBeatNumber')
        if not isinstance(start_beat, (int, float)):
            start_beat = 0
        track = data.get('track')
        if track not in (1, 2, 3):
            track = 2
        
        return cls(
            data_pairs=data_pairs,
            end_beat=end_beat,
            start_beat=start_beat,
            track=track,
            type=type
        )
    
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
