x = 2 + 3
print(x)
print(x > 3)

# TODO:
# make if expression lazily evaluate branches

def gcd(x: float, y: float) -> float:
    print(f'gcd called with {x} and {y}')
    return gcd(y, x % y) if y else x

d = gcd(8 * 9 * x, 4 * 3 * 25)
print(f'x = {x}')
print(f'd = {d}')


# TODO:
# 1. make closures actually copy in their values
# 2. allow nonlocal/global keyword
# 3. allow setting of nonlocal/global variables
# 4. parse +=
count = 1
def make_counter():
    count = 0
    def counter():
        nonlocal count
        count += 1
        return count
    return counter


counter1 = make_counter()
counter2 = make_counter()


print(f'counter1: {counter1()}')
print(f'counter1: {counter1()}')
print(f'counter1: {counter1()}')
print(f'counter1: {counter1()}')
print(f'counter2: {counter2()}')
print(f'counter2: {counter2()}')
print(f'counter1: {counter1()}')
print(f'counter1: {counter1()}')
