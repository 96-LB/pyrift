from pyrift.stubs import set_text, text, wait


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


t1 = text()
t2 = text()
set_text(t2, f'<color=#ff0000>                                          hi')
async def f():
    x = 0
    while x < 10:
        set_text(t1, f'<color=#6df141>{x} seconds...')
        await wait(1)

f()
