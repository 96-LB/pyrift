from pyrift.choreomaps.external import log

x = 2 + 3
log(f'Hello World! {x}')

def inner(x: float, y: float) -> float:
    log(f'inner called with {x} and {y}')
    return x if x % y == 0 else y

a = 2 * 13 * 17 * 9
log(f'Hello World! {x} {a}')
if inner(18, 3):
    log(f'{x} {a}')
    inner(a, 3 * 17 * 8)
else:
    log(f'{x}{x}{x} {a}{a}{a}')
    inner(96, a)

b = 2 if False else 3
log(f'b = {b}')
