from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, ClassVar

from util import snake_to_camel

from .enum import (
    AnimationType,
    BinaryOperator,
    ButtonMask,
    EntityAttribute,
    GraphicType,
    ScoreType,
    SpriteAttribute,
    Statistic,
    Status,
    SystemAttribute,
)

if TYPE_CHECKING:
    from .condition import BaseCondition
    from .value import BaseValue


@dataclass(frozen=True)
class BaseEvent:
    '''
    Attributes:
        TYPE: Event type
        t: Time that the event is triggered, in seconds
    '''
    
    TYPE: ClassVar[str]
    t: float
    
    def __init_subclass__(cls, type: str):
        super().__init_subclass__()
        cls.TYPE = type
    
    def to_dict(self):
        field_values = {snake_to_camel(f.name): getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}
        return {**field_values, 'ev': self.TYPE}


@dataclass(frozen=True)
class SpawnEvent(BaseEvent, type='Spawn'):
    '''
    Attributes:
        type: Type ID of the entity to spawn
        id: ID to be assigned to the spawned entity
        x: X coordinate to spawn entity at (if nil, spawns in the center lane)
        y: Y coordinate to spawn entity at (if nil, defaults to topmost row)
        facing_x: Facing direction to spawn the entity in
    '''
    
    type: BaseValue
    id: BaseValue
    x: BaseValue
    y: BaseValue
    facing_x: BaseValue


@dataclass(frozen=True)
class DespawnEvent(BaseEvent, type='Despawn'):
    '''
    Attributes:
        id: ID of the entity to despawn
    '''
    
    id: BaseValue


@dataclass(frozen=True)
class EntityAttributeEvent(BaseEvent, type='EntityAttribute'):
    '''
    Attributes:
        id: ID of the entity to affect
        attribute: Attribute to modify
        value: Value to set the attribute to
    '''
    
    id: BaseValue
    attribute: EntityAttribute
    value: BaseValue


@dataclass(frozen=True)
class MoveEvent(BaseEvent, type='Move'):
    '''
    Attributes:
        id: ID of the entity to move
        delay: Amount of time to delay this move by
        x: X coordinate to move entity to (if nil, preserves X coordinate)
        y: Y coordinate to move entity to (if nil, preserves Y coordinate)
        facing_x: If set, overrides the facing direction of the enemy alongside the move
        lerp: Interpolation mode for this move
    '''
    
    id: BaseValue
    delay: BaseValue
    x: BaseValue | None = None
    y: BaseValue | None = None
    facing_x: BaseValue | None = None
    lerp: BaseValue | None = None


@dataclass(frozen=True)
class StatusAddEvent(BaseEvent, type='StatusAdd'):
    '''
    Attributes:
        id: ID of the entity to apply the status effect to
        status: Status effect to apply
    '''
    
    id: BaseValue
    status: Status


@dataclass(frozen=True)
class StatusRemoveEvent(BaseEvent, type='StatusRemove'):
    '''
    Attributes:
        id: ID of the entity to remove the status effect from
        status: Status effect to remove
    '''
    
    id: BaseValue
    status: BaseValue


@dataclass(frozen=True)
class HitVfxEvent(BaseEvent, type='HitVfx'):
    '''
    Attributes:
        x: X grid position of the hit
        y: Y grid position of the hit
        rating: Input rating (-1 = miss, 0 = ok, 1 = good, 2 = great, 3 = perfect)
        timing: Input timing (0 = early, 1 = on time, 2 = late)
        true_perfect: Is this a true perfect hit? This produces a slightly different animation
        kill: Should the kill animation play on the affected tile?
        health_item: Should the heal animation play on the affected tile?
        final_hit: Is this one of the final hits of the level?
        lockout: Is this a lockout hit? This produces a miss-like animation on the action row
    '''
    
    x: BaseValue | None = None
    y: BaseValue | None = None
    rating: BaseValue | None = None
    timing: BaseValue | None = None
    true_perfect: BaseCondition | None = None
    kill: BaseCondition | None = None
    health_item: BaseCondition | None = None
    final_hit: BaseCondition | None = None
    lockout: BaseCondition | None = None


@dataclass(frozen=True)
class SoundEvent(BaseEvent, type='Sound'):
    '''
    Attributes:
        sound: Numeric index of the sound effect to play (1-indexed array in Choreomap), 0 to stop an existing sound
        id: Reference number for cancelling a queued sound effect
        delay: Number of seconds for which to queue the sound effect before it is played (defaults to 0)
        apply_latency: Applies the audio latency offset to the specified sound delay (defaults to true)
        fade_in: Number of seconds for which to fade in the sound effect when it plays (defaults to 0)
        lane: Lane number for horizontal panning (0 = left, 1 = center, 2 = right; defaults to 1)
        volume: Volume to play the sound effect at (normalized between 0 and 1, defaults to 1)
        pitch: Pitch to play the sound effect at (defaults to 1)
    '''
    
    sound: BaseValue | None = None
    id: BaseValue | None = None
    delay: BaseValue | None = None
    apply_latency: BaseValue | None = None
    fade_in: BaseValue | None = None
    lane: BaseValue | None = None
    volume: BaseValue | None = None
    pitch: BaseValue | None = None


@dataclass(frozen=True)
class SoundCancelEvent(BaseEvent, type='SoundCancel'):
    '''
    Attributes:
        ids: List of sound effect IDs to cancel
    '''
    
    ids: tuple[BaseValue, ...]


@dataclass(frozen=True)
class AnimateEvent(BaseEvent, type='Animate'):
    '''
    Attributes:
        id: ID of the entity to animate
        type: Name of the animation type to play
    '''
    
    id: BaseValue
    type: AnimationType


@dataclass(frozen=True)
class SpriteEvent(BaseEvent, type='Sprite'):
    '''
    Attributes:
        id: ID of the sprite to affect
        attribute: Attribute to modify
        operator: Binary operator to apply for blending old/new values
        x: X component of the attribute value to assign to the sprite. If nil, preserves the old value
        y: Y component of the attribute value to assign to the sprite. If nil, preserves the old value
        z: Z component of the attribute value to assign to the sprite. If nil, preserves the old value
        w: W component of the attribute value to assign to the sprite. If nil, preserves the old value
    '''
    
    id: BaseValue
    attribute: SpriteAttribute
    operator: BinaryOperator
    x: BaseValue | None = None
    y: BaseValue | None = None
    z: BaseValue | None = None
    w: BaseValue | None = None


@dataclass(frozen=True)
class GraphicCreateEvent(BaseEvent, type='GraphicCreate'):
    '''
    Attributes:
        id: Reference ID of the graphic to create. Distinct from visual IDs. Must be unique
        parent: Visual ID to attach the graphic to. If nil, attaches to the stage root
        type: Subtype of the graphic object to instantiate
    '''
    
    id: BaseValue
    parent: BaseValue | None = None
    type: GraphicType | None = None


@dataclass(frozen=True)
class GraphicDestroyEvent(BaseEvent, type='GraphicDestroy'):
    '''
    Attributes:
        id: Reference ID of the graphic to destroy
    '''
    
    id: BaseValue


@dataclass(frozen=True)
class PlayerHealthEvent(BaseEvent, type='PlayerHealth'):
    '''
    Attributes:
        id: Entity ID inflicting the hit/heal for stat tracking (in case of a player death)
        diff: Amount of health to add (positive) or remove (negative)
    '''
    
    id: BaseValue
    diff: BaseValue


@dataclass(frozen=True)
class ScoreEvent(BaseEvent, type='Score'):
    '''
    Attributes:
        type: Type of score incrementation to perform
        amount: For 'Extra' type scores, exact amount of score to grant to the player
    '''
    
    type: ScoreType
    amount: int | None = None


@dataclass(frozen=True)
class ComboAddEvent(BaseEvent, type='ComboAdd'):
    '''
    Attributes:
    '''


@dataclass(frozen=True)
class ComboDropEvent(BaseEvent, type='ComboDrop'):
    '''
    Attributes:
    '''


@dataclass(frozen=True)
class StatEvent(BaseEvent, type='Stat'):
    '''
    Attributes:
        type: Type name of the entity for which stats should be tracked
        stat: Stat type to increment
        amount: Amount to change stat by (if nil, 1)
    '''
    
    type: str
    stat: Statistic
    amount: int | None = None


@dataclass(frozen=True)
class SystemEvent(BaseEvent, type='System'):
    '''
    Attributes:
        attribute: System attribute to assign
        value: Value to assign to the attribute
    '''
    
    attribute: SystemAttribute
    value: BaseValue


@dataclass(frozen=True)
class FinishLevelEvent(BaseEvent, type='FinishLevel'):
    '''
    Attributes:
        win: If true, the completion counts as a victory
    '''
    
    win: BaseCondition


@dataclass(frozen=True)
class InputOpenEvent(BaseEvent, type='InputOpen'):
    '''
    Attributes:
        id: Unique ID to assign to this input window
        mask: Bitmask of buttons that must be hit for this input window
        rating_id: Index into the inputRatingDefinitions array
        offset: The time offset to apply to this input window
        release_offset: The time offset to apply when checking for button releases on this input window
        priority: Priority value if multiple input windows overlap
        force_split: If set, prevents the 3-lane key (DOWN) from hitting this input window
        on_hit: Stream to start when this input window is hit successfully
        on_release: Stream to start when this input window is released
        on_miss: Stream to start when this input window is missed
    '''
    
    id: BaseValue
    mask: ButtonMask
    rating_id: int
    offset: BaseValue | None = None
    release_offset: BaseValue | None = None
    priority: BaseValue | None = None
    force_split: BaseCondition | None = None
    on_hit: BaseEvent | None = None
    on_release: BaseEvent | None = None
    on_miss: BaseEvent | None = None


@dataclass(frozen=True)
class InputCloseEvent(BaseEvent, type='InputClose'):
    '''
    Attributes:
        id: Unique ID of the input window to close
    '''
    
    id: BaseValue


@dataclass(frozen=True)
class StartStreamEvent(BaseEvent, type='StartStream'):
    '''
    Attributes:
        id: ID of the event stream to start
        ref_id: Reference ID of the event stream to start (for later stopping)
        immediate: If true, immediately processes the stream's events prior to resuming execution
        locals: Optional list of local variables to initialize the stream with
    '''
    
    id: BaseValue
    ref_id: BaseValue
    immediate: BaseCondition
    locals: tuple[BaseValue, ...] | None = None
    
    def to_obj(self):
        dict = self.to_dict()
        ref_id = dict.pop('refId')
        dict['refID'] = ref_id
        return dict


@dataclass(frozen=True)
class StopStreamEvent(BaseEvent, type='StopStream'):
    '''
    Attributes:
        ref_id: Reference ID of the event stream to stop (or nil to stop own stream)
    '''
    
    ref_id: BaseValue | None = None
    
    def to_obj(self):
        dict = self.to_dict()
        ref_id = dict.pop('refId')
        dict['refID'] = ref_id
        return dict

@dataclass(frozen=True)
class IfEvent(BaseEvent, type='If'):
    '''
    Attributes:
        condition: Condition to check
        yes: Event to execute if condition is met
        no: Event to execute if condition is not met
    '''
    
    condition: BaseCondition
    yes: BaseEvent | None
    no: BaseEvent | None


@dataclass(frozen=True)
class JumpEvent(BaseEvent, type='Jump'):
    '''
    Attributes:
        target: Instruction index to jump to
    '''
    
    target: BaseValue


@dataclass(frozen=True)
class WaitEvent(BaseEvent, type='Wait'):
    '''
    Attributes:
        condition: Waits until this condition is true. If nil, waits for one tick instead
    '''
    
    condition: BaseCondition | None = None


@dataclass(frozen=True)
class SetArrayEvent(BaseEvent, type='SetArray'):
    '''
    Attributes:
        name: Name of the array to modify, or nil for the stream's local variables array
        index: Array index to modify, or nil for resizing the array
        value: Value to write to the array
    '''
    
    name: str | None = None
    index: BaseValue | None = None
    value: BaseValue | None = None


@dataclass(frozen=True)
class SetVariableEvent(BaseEvent, type='SetVariable'):
    '''
    Attributes:
        name: Name of the variable to assign
        value: Value to write to the variable
    '''
    
    name: str
    value: BaseValue


@dataclass(frozen=True)
class LogEvent(BaseEvent, type='Log'):
    '''
    Attributes:
        text: Text to write to the log (use {0}, {1}, etc. for placeholders)
        args: Optional list of values to populate placeholders
    '''
    
    text: str
    args: tuple[BaseValue, ...] | None = None
