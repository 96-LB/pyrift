from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from pyrift.jobj import JObj, JList

from ..enum import ComparisonMode, EntityPredicate, SystemPredicate

if TYPE_CHECKING:
    from .value import BaseValue


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

class ConstantCondition(BaseCondition, type='Constant'):
    '''
    Attributes:
        value: Logical constant value
    '''
    
    value: bool
    
    @override
    def to_json_obj(self):
        return self.value


class AndCondition(BaseCondition, type='And'):
    '''
    Attributes:
        conditions: Conditions that must all be fulfilled
    '''
    
    conditions: JList[BaseCondition]


class OrCondition(BaseCondition, type='Or'):
    '''
    Attributes:
        conditions: Conditions of which at least one must be fulfilled
    '''
    
    conditions: JList[BaseCondition]


class NotCondition(BaseCondition, type='Not'):
    '''
    Attributes:
        condition: BaseCondition that must not be fulfilled
    '''
    
    condition: BaseCondition


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


class EntityCondition(BaseCondition, type='Entity'):
    '''
    Attributes:
        id: Entity ID to check
        predicate: Predicate to check for this entity
    '''
    
    id: BaseValue
    predicate: EntityPredicate


class SystemCondition(BaseCondition, type='System'):
    '''
    Attributes:
        predicate: System predicate to check
    '''
    
    predicate: SystemPredicate
