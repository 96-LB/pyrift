from pyrift.choreomaps.globals import log

x = 2 + 3
log(f'Hello World! {x}')

def gcd(x: float, y: float) -> float:
    log(f'gcd called with {x} and {y}')
    return x if y == 0 else gcd(y, x % y)

a = 2 * 13 * 17 * 9
log(f'Hello World! {x} {a}')
if a and 0 and 1 or True or False and a and not a:
    log(f'{x} {a}')
    gcd(a, 3 * 17 * 8)
else:
    log(f'{x}{x}{x} {a}{a}{a}')
    gcd(96, a)

b = 2 if False else 3
log(f'b = {b}')
