from typing import Coroutine

from pyrift.choreomaps.external import wait


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


async def foo():
    print('waiting 1 second...')
    await wait(1)
    print('waiting 2 seconds...')
    await wait(2)
    print('waiting 3 seconds...')
    await wait(3)
    print('returning!')
    return 96


async def wait_for[T](coroutine: Coroutine[None, None, T]) -> T:
    print(f'waiting on coroutine {coroutine}')
    x = await coroutine
    print(f'coroutine {coroutine} returned value {x}')
    return x

print('hi!')
wait_for(foo())
