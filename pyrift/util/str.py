def snake_to_camel(string: str) -> str:
    if string.startswith('_'):
        return string
    components = string.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])

def snake_to_pascal(string: str) -> str:
    if string.startswith('_'):
        return string
    components = string.split('_')
    return ''.join(word.capitalize() for word in components)

def camel_to_snake(string: str) -> str:
    return ''.join('_' + c.lower() for c in string).lstrip('_')