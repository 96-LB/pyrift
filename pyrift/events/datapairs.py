from typing import Sequence, Any

from typeddicts import EventDataPairDict


class DataPairs:
    @classmethod
    def parse(cls, data: Sequence[Any]):
        datapairs = cls()
        for pair in data:
            match pair:
                case {'_eventDataKey': str() as key, '_eventDataValue': str() as value}:
                    datapairs.add(key, value)
                case _:
                    pass
        return datapairs
    
    def __init__(self):
        self.data: dict[str, list[str]] = {}
    
    def add(self, key: str, value: str | float | bool) -> None:
        self.data.setdefault(key, []).append(str(value))
    
    def to_list(self) -> list[EventDataPairDict]:
        return [{'_eventDataKey': k, '_eventDataValue': x} for k, v in self.data.items() for x in v]
    