def snake_to_camel(string: str):
    if string.startswith('_'):
        return string
    components = string.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])
