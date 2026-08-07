from pyrift.choreomaps.globals import log


def inner(x: float, y: float):
    log('inner called with {0} and {1}', x, y)

a = 2 + 3
if a:
    inner(a, 4)
else:
    inner(96, a)

b = 2 if True else 3
log('b = {0}', b)