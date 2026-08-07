from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, ClassVar

from util import snake_to_camel

from .enum import ComparisonMode, EntityPredicate, SystemPredicate

if TYPE_CHECKING:
    from .value import BaseValue


@dataclass(frozen=True)
class BaseCondition:
    '''
    Attributes:
        TYPE: Condition type
    '''
    
    TYPE: ClassVar[str]
    
    def __init_subclass__(cls, type: str):
        super().__init_subclass__()
        cls.TYPE = type
    
    def to_dict(self):
        field_values = {snake_to_camel(f.name): getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}
        return {**field_values, 'type': self.TYPE}

@dataclass(frozen=True)
class ConstantCondition(BaseCondition, type='Constant'):
    '''
    Attributes:
        value: Logical constant value
    '''
    
    value: bool
    
    def to_obj(self):
        return self.value


@dataclass(frozen=True)
class AndCondition(BaseCondition, type='And'):
    '''
    Attributes:
        conditions: Conditions that must all be fulfilled
    '''
    
    conditions: tuple[BaseCondition, ...]


@dataclass(frozen=True)
class OrCondition(BaseCondition, type='Or'):
    '''
    Attributes:
        conditions: Conditions of which at least one must be fulfilled
    '''
    
    conditions: tuple[BaseCondition, ...]


@dataclass(frozen=True)
class NotCondition(BaseCondition, type='Not'):
    '''
    Attributes:
        condition: BaseCondition that must not be fulfilled
    '''
    
    condition: BaseCondition


@dataclass(frozen=True)
class CompareCondition(BaseCondition, type='Compare'):
    '''
    Attributes:
        value1: Left-hand side of the comparison
        value2: Right-hand side of the comparison
        mode: Comparison operator to apply
    '''
    
    value1: BaseValue
    value2: BaseValue
    mode: ComparisonMode


@dataclass(frozen=True)
class EntityCondition(BaseCondition, type='Entity'):
    '''
    Attributes:
        id: Entity ID to check
        predicate: Predicate to check for this entity
    '''
    
    id: BaseValue
    predicate: EntityPredicate


@dataclass(frozen=True)
class SystemCondition(BaseCondition, type='System'):
    '''
    Attributes:
        predicate: System predicate to check
    '''
    
    predicate: SystemPredicate
