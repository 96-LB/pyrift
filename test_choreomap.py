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


def f():
    x = 2
    if x:
        x = wait(2)
        print(x)

f()
