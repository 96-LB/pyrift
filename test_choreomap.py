from typing import Coroutine

from pyrift.choreomaps.external import wait


x = [1]


# TODO:
# 1. test existing code (async functions, fix for heap allocation, dynamic matching, etc.)
# 2. exceptions
# 3. arrays
# 4. property access
# 5. basic builtins for interacting with the game
# 6. classes
# 7. dictionaries
# 8. sets
# 9. type-checking



# x = 1
# async def f():
#     await x


# async def normal():
#     print(0)
#     await wait(1)
#     print(1)
#     await wait(2)
#     print(2)
#     return 3


# async def wrap[T](coroutine: Coroutine[None, None, T]) -> T:
#     print('starting')
#     x = await coroutine
#     print(x)
#     print('ending')
#     return x


# _ = wrap(normal())
