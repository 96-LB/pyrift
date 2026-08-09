from abc import ABC
from dataclasses import dataclass, fields, replace
from typing import Any, Self, dataclass_transform

from pyrift.util import snake_to_camel


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