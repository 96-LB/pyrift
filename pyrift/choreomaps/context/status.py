from enum import Enum, auto


class ContextStatus(Enum):
    INACTIVE = auto()
    ACTIVE = auto()
    FINISHED = auto()