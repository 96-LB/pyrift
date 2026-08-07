from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from .enum import ComparisonMode, EntityPredicate, SystemPredicate

if TYPE_CHECKING:
    from .types import Condition, Value


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


@dataclass(frozen=True)
class ConstantCondition(BaseCondition, type='Constant'):
    '''
    Attributes:
        value: Logical constant value
    '''
    
    value: bool


@dataclass(frozen=True)
class AndCondition(BaseCondition, type='And'):
    '''
    Attributes:
        conditions: Conditions that must all be fulfilled
    '''
    
    conditions: list[Condition]


@dataclass(frozen=True)
class OrCondition(BaseCondition, type='Or'):
    '''
    Attributes:
        conditions: Conditions of which at least one must be fulfilled
    '''
    
    conditions: list[Condition]


@dataclass(frozen=True)
class NotCondition(BaseCondition, type='Not'):
    '''
    Attributes:
        condition: Condition that must not be fulfilled
    '''
    
    condition: Condition


@dataclass(frozen=True)
class CompareCondition(BaseCondition, type='Compare'):
    '''
    Attributes:
        value1: Left-hand side of the comparison
        value2: Right-hand side of the comparison
        mode: Comparison operator to apply
    '''
    
    value1: Value
    value2: Value
    mode: ComparisonMode


@dataclass(frozen=True)
class EntityCondition(BaseCondition, type='Entity'):
    '''
    Attributes:
        id: Entity ID to check
        predicate: Predicate to check for this entity
    '''
    
    id: Value
    predicate: EntityPredicate


@dataclass(frozen=True)
class SystemCondition(BaseCondition, type='System'):
    '''
    Attributes:
        predicate: System predicate to check
    '''
    
    predicate: SystemPredicate
