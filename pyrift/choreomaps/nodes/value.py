from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from .enum import BinaryOperator, EntityAttribute, SpriteAttribute, SystemAttribute, UnaryOperator, VisualType

if TYPE_CHECKING:
    from .types import Condition, Value


@dataclass(frozen=True)
class BaseValue:
    '''
    Attributes:
        TYPE: Value type
    '''
    
    TYPE: ClassVar[str]
    
    def __init_subclass__(cls, type: str):
        super().__init_subclass__()
        cls.TYPE = type


@dataclass(frozen=True)
class ConstantValue(BaseValue, type='Constant'):
    '''
    Attributes:
        value: Numeric value
    '''
    
    value: float


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class UnaryValue(BaseValue, type='Unary'):
    """
    Attributes:
        value: Numeric value.
        operator: Math operation to apply.
    """
    
    value: Value
    operator: UnaryOperator


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class VariableValue(BaseValue, type='Variable'):
    """
    Attributes:
        name: Name of the variable to read from.
    """
    
    name: str


@dataclass(frozen=True)
class ArrayValue(BaseValue, type='Array'):
    """
    Attributes:
        name: Name of the array to read from, or nil to read the local variable array.
        index: Index to read from, or nil to read the array's length.
    """
    
    name: str | None = None
    index: BaseValue | None = None


@dataclass(frozen=True)
class EntityValue(BaseValue, type='Entity'):
    """
    Attributes:
        id: Entity ID to read from.
        attribute: Entity attribute to read.
    """
    
    id: Value
    attribute: EntityAttribute


@dataclass(frozen=True)
class SystemValue(BaseValue, type='System'):
    """
    Attributes:
        attribute: System attribute to read.
    """
    
    attribute: SystemAttribute


@dataclass(frozen=True)
class SpriteIDValue(BaseValue, type='SpriteID'):
    """
    Attributes:
        visualType: Visual type to obtain a reference to.
        x: Primary parameter for resolving specific sub-sprites, such as grid lane or graphic ID.
        y: Secondary parameter for resolving specific sub-sprites, such as grid row.
    """
    
    visualType: VisualType
    x: BaseValue | None = None
    y: BaseValue | None = None


@dataclass(frozen=True)
class SpriteFindIDValue(BaseValue, type='SpriteFindID'):
    """
    Attributes:
        id: Sprite ID to start the search from. If nil, starts from the root. If 0, never returns results.
        path: Name of the object to locate (uses Unity GameObject names). If nil, returns the specified object (or scene root) directly if it exists, and 0 if destroyed.
    """
    
    id: Value
    path: str | None = None


@dataclass(frozen=True)
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
