from __future__ import annotations

from types import NotImplementedType
from typing import TYPE_CHECKING, ClassVar, override

from pyrift.jobj import JObj

from ..enum import (
    BinaryOperator,
    ComparisonMode,
    EntityAttribute,
    SpriteAttribute,
    SystemAttribute,
    UnaryOperator,
    VisualType,
)
from .condition import CompareCondition

if TYPE_CHECKING:
    from .condition import Condition
    from .string import String


type Value = float | BaseValue
type TaggedValue = tuple[Value, Value | Condition | String]

class BaseValue(JObj):
    '''
    Attributes:
        TYPE: Value type
    '''
    
    TYPE: ClassVar[str]
    
    def __init_subclass__(cls, type: str):
        super().__init_subclass__()
        cls.TYPE = type
    
    @override
    def to_dict(self):
        return {**super().to_dict(), 'type': self.TYPE}
    
    def compare(self, value: object, mode: ComparisonMode) -> CompareCondition | NotImplementedType:
        '''
        Creates a symbolic comparison between this value and another.
        '''
        if isinstance(value, (BaseValue, int, float)):
            return CompareCondition(self, value, mode)
        return NotImplemented

    def __eq__(self, value: object) -> CompareCondition | NotImplementedType:
        return self.compare(value, ComparisonMode.EQUAL)
    
    def __ne__(self, value: object) -> CompareCondition | NotImplementedType:
        return self.compare(value, ComparisonMode.NOT_EQUAL)
    
    def __lt__(self, value: object) -> CompareCondition | NotImplementedType:
        return self.compare(value, ComparisonMode.LESS)
    
    def __le__(self, value: object) -> CompareCondition | NotImplementedType:
        return self.compare(value, ComparisonMode.LESS_EQUAL)
    
    def __gt__(self, value: object) -> CompareCondition | NotImplementedType:
        return self.compare(value, ComparisonMode.GREATER)
    
    def __ge__(self, value: object) -> CompareCondition | NotImplementedType:
        return self.compare(value, ComparisonMode.GREATER_EQUAL)
    
    def __add__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.ADD)
    
    def __radd__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.ADD)

    def __sub__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.SUBTRACT)
    
    def __rsub__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.SUBTRACT)

    def __mul__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.MULTIPLY)
    
    def __rmul__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.MULTIPLY)
    
    def __truediv__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.DIVIDE)
    
    def __rtruediv__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.DIVIDE)
    
    def __mod__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.MOD)
    
    def __rmod__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.MOD)
    
    def __pow__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.POWER)
    
    def __rpow__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.POWER)
    
    def __or__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.OR)
    
    def __ror__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.OR)
    
    def __and__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.AND)
    
    def __rand__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.AND)
    
    def __lshift__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.L_SHIFT)
    
    def __rlshift__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.L_SHIFT)
    
    def __rshift__(self, value: Value) -> MathValue:
        return MathValue(self, value, BinaryOperator.R_SHIFT)
    
    def __rrshift__(self, value: Value) -> MathValue:
        return MathValue(value, self, BinaryOperator.R_SHIFT)
    
    def __abs__(self) -> UnaryValue:
        return UnaryValue(self, UnaryOperator.ABS)
    
    def __floor__(self) -> UnaryValue:
        return UnaryValue(self, UnaryOperator.FLOOR)
    
    def __ceil__(self) -> UnaryValue:
        return UnaryValue(self, UnaryOperator.CEIL)
    
    def __invert__(self):
        return UnaryValue(self, UnaryOperator.NOT)
    
    def __neg__(self):
        return UnaryValue(self, UnaryOperator.NEG)
    
    def __pos__(self):
        return self


class MathValue(BaseValue, type='Math'):
    '''
    Attributes:
        value1: Left operand.
        value2: Right operand.
        operator: Math operation to apply.
    '''
    
    value1: Value
    value2: Value
    operator: BinaryOperator


class UnaryValue(BaseValue, type='Unary'):
    '''
    Attributes:
        value: Numeric value.
        operator: Math operation to apply.
    '''
    
    value: Value
    operator: UnaryOperator


class IfValue(BaseValue, type='If'):
    '''
    Attributes:
        condition: Condition to check.
        yes: Value if the condition is true.
        no: Value if the condition is false.
    '''
    
    condition: Condition
    yes: Value
    no: Value


class VariableValue(BaseValue, type='Variable'):
    '''
    Attributes:
        name: Name of the variable to read from.
    '''
    
    __eq__ = BaseValue.__eq__ # suppresses pyright warnings in compiler.py
    
    name: String


class ArrayValue(BaseValue, type='Array'):
    '''
    Attributes:
        name: Name of the array to read from, or nil to read the local variable array.
        index: Index to read from, or nil to read the array's length.
    '''
    
    __eq__ = BaseValue.__eq__ # suppresses pyright warnings in compiler.py
    
    name: String | None = None
    index: Value | None = None


class EntityValue(BaseValue, type='Entity'):
    '''
    Attributes:
        id: Entity ID to read from.
        attribute: Entity attribute to read.
    '''
    
    id: Value
    attribute: EntityAttribute


class SystemValue(BaseValue, type='System'):
    '''
    Attributes:
        attribute: System attribute to read.
    '''
    
    attribute: SystemAttribute


class SpriteIDValue(BaseValue, type='SpriteID'):
    '''
    Attributes:
        visualType: Visual type to obtain a reference to.
        x: Primary parameter for resolving specific sub-sprites, such as grid lane or graphic ID.
        y: Secondary parameter for resolving specific sub-sprites, such as grid row.
    '''
    
    visualType: VisualType
    x: Value | None = None
    y: Value | None = None


class SpriteFindIDValue(BaseValue, type='SpriteFindID'):
    '''
    Attributes:
        id: Sprite ID to start the search from. If nil, starts from the root. If 0, never returns results.
        path: Name of the object to locate (uses Unity GameObject names). If nil, returns the specified object (or scene root) directly if it exists, and 0 if destroyed.
    '''
    
    id: Value
    path: String | None = None


class SpriteAttributeValue(BaseValue, type='SpriteAttribute'):
    '''
    Attributes:
        id: Sprite ID to read from.
        attribute: Sprite attribute to read.
        index: Component index to read (0 = X, 1 = Y, 2 = Z, 3 = W). Defaults to X.
    '''
    
    id: Value
    attribute: SpriteAttribute
    index: Value | None = None
