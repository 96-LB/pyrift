from enum import Enum, IntEnum, auto


class Tag(IntEnum):
    NONE = 0
    NUMBER = -1
    STRING = -2
    FUNCTION = -3
    COROUTINE = -4
    ARRAY = -5
    OBJECT = -6


class VarType(Enum):
    LOCAL = auto()
    CAPTURED = auto()
    NONLOCAL = auto()
    GLOBAL = auto()
    EXTERNAL = auto()
