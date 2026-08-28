from collections.abc import Callable, Coroutine, Iterator
from types import EllipsisType
from typing import Any

type F[**P, T] = Callable[P, T]
type G[**P, T] = F[P, Iterator[T]]
type C[T] = Coroutine[Any, Any, T]
type AF[**P, T] = F[P, C[T]]
type E = EllipsisType
type AnyF = F[..., Any]
type NullF = F[[], None]
