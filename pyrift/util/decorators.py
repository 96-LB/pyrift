from functools import wraps
from inspect import (
    iscoroutinefunction,
    markcoroutinefunction,
)
from typing import Concatenate

from .typing import AnyF, F


def copycoroutine[F2: AnyF](source: AnyF) -> F[[F2], F2]:
    '''Copies the coroutine status of the input function to the decorated function.'''
    
    @wraps(source)
    def decorator(dest: F2) -> F2:
        return markcoroutinefunction(dest) if iscoroutinefunction(source) else dest
    return decorator


def decorates[T, R, **P, **Q](func: F[Concatenate[F[P, T], Q], R]) -> F[[F[P, T]], F[Q, R]]:
    @wraps(func)
    def decorator(view: F[P, T]) -> F[Q, R]:
        @wraps(view)
        @copycoroutine(func)
        def wrapper(*args: Q.args, **kwargs: Q.kwargs) -> R:
            return func(view, *args, **kwargs)
        return wrapper
    return decorator


def decorates_self[T, S, R, **P, **Q](func: F[Concatenate[S, F[P, T], Q], R]) -> F[[S, F[P, T]], F[Q, R]]:
    @wraps(func)
    def decorator(self: S, view: F[P, T]) -> F[Q, R]:
        @wraps(view)
        @copycoroutine(func)
        def wrapper(*args: Q.args, **kwargs: Q.kwargs) -> R:
            return func(self, view, *args, **kwargs)
        return wrapper
    return decorator
