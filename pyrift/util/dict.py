from typing import overload


_MISSING = object() # TODO: python 3.15 sentinel

@overload
def get_first[T, U](dict: dict[T, U], *args: T) -> U: ...

@overload
def get_first[T, U, V](dict: dict[T, U], *args: T, default: V) -> U | V: ...

def get_first[T, U, V](dict: dict[T, U], *args: T, default: V = _MISSING) -> U | V:
    for arg in args:
        if arg in dict:
            return dict[arg]
    if default is not _MISSING:
        return default
    raise KeyError('None of the provided keys were found in the dictionary.')
