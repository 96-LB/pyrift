from enum import Enum, IntEnum, auto


class Tag(IntEnum):
    NONE = 0
    NUMBER = -1
    STRING = -2
    ARRAY = -3
    FUNCTION = -4
    OBJECT = -5


class VarType(Enum):
    LOCAL = auto()
    CAPTURED = auto()
    NONLOCAL = auto()
    GLOBAL = auto()
    EXTERNAL = auto()
