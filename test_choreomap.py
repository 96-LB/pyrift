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


j = ['1', '2', '3']
k = len(j)
l = len('123')
print(f'testing {k} and {l}')

obj = text()

async def display_time(max: float):
    x = 0
    while x <= max:
        print(x)
        set_text(obj, f'<color=#6df141><b><size=96px>{x} seconds...<sprite=6 color=#416df1>')
        await wait(0.1)
        x += 0.1
    print(x)

if 1 or 2 and None or False:
    print(1 or 2 and None or False)