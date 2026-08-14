from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from pyrift.jobj import JObj

from ..enum import (
    BinaryOperator,
    EntityAttribute,
    SpriteAttribute,
    SystemAttribute,
    UnaryOperator,
    VisualType,
)

if TYPE_CHECKING:
    from .condition import Condition
    from .string import String


type Value = float | BaseValue

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


# class ConstantValue(BaseValue, type='Constant'):
#     '''
#     Attributes:
#         value: Numeric value
#     '''
    
#     value: float
    
#     @override
#     def to_json_obj(self):
#         return self.value


class MathValue(BaseValue, type='Math'):
    """
    Attributes:
        value1: Left operand.
        value2: Right operand.
        operator: Math operation to apply.
    """
    
    value1: Value
    value2: Value
    operator: BinaryOperator


class UnaryValue(BaseValue, type='Unary'):
    """
    Attributes:
        value: Numeric value.
        operator: Math operation to apply.
    """
    
    value: Value
    operator: UnaryOperator


class IfValue(BaseValue, type='If'):
    """
    Attributes:
        condition: Condition to check.
        yes: Value if the condition is true.
        no: Value if the condition is false.
    """
    
    condition: Condition
    yes: Value
    no: Value


class VariableValue(BaseValue, type='Variable'):
    """
    Attributes:
        name: Name of the variable to read from.
    """
    
    name: str


class ArrayValue(BaseValue, type='Array'):
    """
    Attributes:
        name: Name of the array to read from, or nil to read the local variable array.
        index: Index to read from, or nil to read the array's length.
    """
    
    name: String | None = None
    index: Value | None = None


class EntityValue(BaseValue, type='Entity'):
    """
    Attributes:
        id: Entity ID to read from.
        attribute: Entity attribute to read.
    """
    
    id: Value
    attribute: EntityAttribute


class SystemValue(BaseValue, type='System'):
    """
    Attributes:
        attribute: System attribute to read.
    """
    
    attribute: SystemAttribute


class SpriteIDValue(BaseValue, type='SpriteID'):
    """
    Attributes:
        visualType: Visual type to obtain a reference to.
        x: Primary parameter for resolving specific sub-sprites, such as grid lane or graphic ID.
        y: Secondary parameter for resolving specific sub-sprites, such as grid row.
    """
    
    visualType: VisualType
    x: Value | None = None
    y: Value | None = None


class SpriteFindIDValue(BaseValue, type='SpriteFindID'):
    """
    Attributes:
        id: Sprite ID to start the search from. If nil, starts from the root. If 0, never returns results.
        path: Name of the object to locate (uses Unity GameObject names). If nil, returns the specified object (or scene root) directly if it exists, and 0 if destroyed.
    """
    
    id: Value
    path: str | None = None


class SpriteAttributeValue(BaseValue, type='SpriteAttribute'):
    """
    Attributes:
        id: Sprite ID to read from.
        attribute: Sprite attribute to read.
        index: Component index to read (0 = X, 1 = Y, 2 = Z, 3 = W). Defaults to X.
    """
    
    id: Value
    attribute: SpriteAttribute
    index: Value | None = None
