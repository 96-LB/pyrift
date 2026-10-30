from abc import ABC
from dataclasses import dataclass, fields, replace
from types import GenericAlias, UnionType
from typing import Any, NoReturn, Self, dataclass_transform, get_args, get_origin

from pyrift.util.str import snake_to_camel, snake_to_pascal

from .util.dict import get_first

type JsonT = str | int | float | bool | list[JsonT] | dict[str, JsonT] | None
type JList[T] = tuple[T, ...]

@dataclass_transform(frozen_default=True)
@dataclass(frozen=True)
class JObj(ABC):
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        
        dataclass(frozen=True)(cls)
    
    def but(self, **attrs: Any) -> Self:
        return replace(self, **attrs)
    
    def plus(self, **attrs: Any) -> Self:
        for name, attr in attrs.items():
            attrs[name] = getattr(self, name) + attr
        return self.but(**attrs)
    
    def to_dict(self) -> dict[str, JsonT]:
        field_values = {snake_to_camel(f.name): getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}
        return field_values
    
    def to_json_obj(self) -> JsonT:
        return self.to_dict()
    
    @classmethod
    def from_json(cls, json_obj: dict[str, JsonT]) -> Self:
        params = {}
        for field in fields(cls):
            name = field.name
            obj = get_first(json_obj, field.name, field.name.upper(), snake_to_camel(field.name), snake_to_pascal(field.name), default=...)
            
            if obj is ...:
                continue
            
            params[name] = JObj.convert(obj, field.type, field=f'{cls.__name__}.{name}')
        
        return cls(**params)
    
    @staticmethod
    def convert(obj: JsonT, target: Any, *, field: str | None) -> Any:
        def error(msg: str) -> NoReturn:
            prefix = f'Failed to parse field {field}. ' if field else f'Failed to convert {obj} to {target.__name__}. '
            raise ValueError(prefix + msg)
        
        if isinstance(target, type):
            if issubclass(target, JObj):
                if isinstance(obj, dict):
                    return target.from_json(obj)
                else:
                    error(f'Expected dict, got {type(obj).__name__}.')
            if isinstance(obj, (float, int) if target is float else target):
                return obj
            else:
                error(f'Expected {target.__name__}, got {type(obj).__name__}.')
        elif isinstance(target, GenericAlias):
            origin = get_origin(target)
            args = get_args(target)
            
            if origin is list:
                if isinstance(obj, list):
                    return [JObj.convert(item, args[0], field=field) for item in obj]
                else:
                    error(f'Expected list, got {type(obj).__name__}.')
            elif origin is dict:
                if isinstance(obj, dict):
                    return {k: JObj.convert(v, args[1], field=field) for k, v in obj.items()}
                else:
                    error(f'Expected dict, got {type(obj).__name__}.')
            else:
                error(f'Unknown generic type {target}.')
        elif isinstance(target, UnionType):
            args = get_args(target)
            for arg in args:
                try:
                    return JObj.convert(obj, arg, field=field)
                except ValueError:
                    continue
            error(f'Failed to convert {obj} to any of the union types {args}.')
        
        else:
            error(f'Unknown target type {target}.')
