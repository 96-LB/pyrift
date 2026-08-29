from typing import Coroutine

from pyrift.choreomaps.external import set_text, text, wait


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


obj2 = text()
set_text(obj2, "Hello, World!")
print(f'created {obj2}')


obj = text()
def display(text: str):
    print(text)
    set_text(obj, text)


async def foo():
    display('waiting 1 second...')
    await wait(1)
    display('waiting 2 seconds...')
    await wait(2)
    display('waiting 3 seconds...')
    await wait(3)
    display('returning!')
    return 96


async def wait_for[T](coroutine: Coroutine[None, None, T]) -> T:
    display(f'waiting on coroutine {coroutine}')
    x = await coroutine
    display(f'coroutine {coroutine} returned value {x}')
    return x

display('hi!')
wait_for(foo())
