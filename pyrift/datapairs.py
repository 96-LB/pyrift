from .typeddicts import EventDataPairDict


class DataPairs:
    def __init__(self):
        self.data: dict[str, list[str]] = {}
    
    def add(self, key: str, value: str | float | bool) -> None:
        self.data.setdefault(key, []).append(str(value))
    
    def to_list(self) -> list[EventDataPairDict]:
        return [{'_eventDataKey': k, '_eventDataValue': x} for k, v in self.data.items() for x in v]
