from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from pyrift.jobj import JList, JObj

from ..enum import ComparisonMode, EntityPredicate, SystemPredicate

if TYPE_CHECKING:
    from .value import Value


type Condition = bool | BaseCondition

class BaseCondition(JObj):
    '''
    Attributes:
        TYPE: Condition type
    '''
    
    TYPE: ClassVar[str]
    
    def __init_subclass__(cls, type: str):
        super().__init_subclass__()
        cls.TYPE = type
    
    @override
    def to_dict(self):
        return {**super().to_dict(), 'type': self.TYPE}
    
    def __invert__(self) -> NotCondition:
        return NotCondition(self)
    
    def __and__(self, condition: Condition) -> AndCondition:
        return AndCondition((self, condition))
    
    def __or__(self, condition: Condition) -> OrCondition:
        return OrCondition((self, condition))


class AndCondition(BaseCondition, type='And'):
    '''
    Attributes:
        conditions: Conditions that must all be fulfilled
    '''
    
    conditions: JList[Condition]


class OrCondition(BaseCondition, type='Or'):
    '''
    Attributes:
        conditions: Conditions of which at least one must be fulfilled
    '''
    
    conditions: JList[Condition]


class NotCondition(BaseCondition, type='Not'):
    '''
    Attributes:
        condition: BaseCondition that must not be fulfilled
    '''
    
    condition: Condition


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


class EntityCondition(BaseCondition, type='Entity'):
    '''
    Attributes:
        id: Entity ID to check
        predicate: Predicate to check for this entity
    '''
    
    id: Value
    predicate: EntityPredicate


class SystemCondition(BaseCondition, type='System'):
    '''
    Attributes:
        predicate: System predicate to check
    '''
    
    predicate: SystemPredicate
