from pyrift.choreomaps.globals import log


x = 2 + 3
log('Hello World! {0}', x)

def inner(x: float, y: float):
    log('inner called with {0} and {1}', x, y)

a = 2 * 3
log('Hello World! {0} {1}', x, a)
if a:
    log('{0} {1}', x, a)
    inner(a, 4)
else:
    log('{0}{0}{0} {1}{1}{1}', x, a)
    inner(96, a)

b = 2 if False else 3
log('b = {0}', b)
