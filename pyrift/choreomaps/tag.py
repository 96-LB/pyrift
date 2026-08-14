from enum import IntEnum


class Tag(IntEnum):
    NONE = 0
    NUMBER = -1
    STRING = -2
    ARRAY = -3
    FUNCTION = -4
    OBJECT = -5
