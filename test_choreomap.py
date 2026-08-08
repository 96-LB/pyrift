from pyrift.choreomaps.globals import log

x = 2 + 3
log('Hello World! {0}', x)

def gcd(x: float, y: float) -> float:
    log('gcd called with {0} and {1}', x, y)
    return x if y == 0 else gcd(y, x % y)

a = 2 * 13 * 17 * 9
log('Hello World! {0} {1}', x, a)
if a and 0 and 1 or True or False and a and not a:
    log('{0} {1}', x, a)
    gcd(a, 3 * 17 * 8)
else:
    log('{0}{0}{0} {1}{1}{1}', x, a)
    gcd(96, a)

b = 2 if False else 3
log('b = {0}', b)
