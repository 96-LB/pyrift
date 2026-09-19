from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from pyrift.jobj import JList, JObj

from ..enum import (
    AnimationType,
    BinaryOperator,
    ButtonMask,
    EntityAttribute,
    GraphicType,
    MoveLerp,
    ScoreType,
    SpriteAttribute,
    SpriteStringAttribute,
    Statistic,
    Status,
    SystemAttribute,
)
from .string import String

if TYPE_CHECKING:
    from .condition import Condition
    from .value import Value


class BaseEvent(JObj):
    '''
    Attributes:
        TYPE: Event type
    '''
    
    TYPE: ClassVar[str]
    
    def __init_subclass__(cls, type: str):
        super().__init_subclass__()
        cls.TYPE = type
    
    @override
    def to_dict(self):
        return {**super().to_dict(), 'ev': self.TYPE}


class SpawnEvent(BaseEvent, type='Spawn'):
    '''
    Attributes:
        type: Type ID of the entity to spawn
        id: ID to be assigned to the spawned entity
        x: X coordinate to spawn entity at (if nil, spawns in the center lane)
        y: Y coordinate to spawn entity at (if nil, defaults to topmost row)
        facing_x: Facing direction to spawn the entity in
    '''
    
    type: Value
    id: Value
    x: Value
    y: Value
    facing_x: Value


class DespawnEvent(BaseEvent, type='Despawn'):
    '''
    Attributes:
        id: ID of the entity to despawn
    '''
    
    id: Value


class EntityAttributeEvent(BaseEvent, type='EntityAttribute'):
    '''
    Attributes:
        id: ID of the entity to affect
        attribute: Attribute to modify
        value: Value to set the attribute to
    '''
    
    id: Value
    attribute: EntityAttribute
    value: Value


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
    
    id: Value
    delay: Value
    x: Value | None = None
    y: Value | None = None
    facing_x: Value | None = None
    lerp: MoveLerp | None = None


class StatusAddEvent(BaseEvent, type='StatusAdd'):
    '''
    Attributes:
        id: ID of the entity to apply the status effect to
        status: Status effect to apply
    '''
    
    id: Value
    status: Status


class StatusRemoveEvent(BaseEvent, type='StatusRemove'):
    '''
    Attributes:
        id: ID of the entity to remove the status effect from
        status: Status effect to remove
    '''
    
    id: Value
    status: Status


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
    
    x: Value | None = None
    y: Value | None = None
    rating: Value | None = None
    timing: Value | None = None
    true_perfect: Condition | None = None
    kill: Condition | None = None
    health_item: Condition | None = None
    final_hit: Condition | None = None
    lockout: Condition | None = None


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
    
    sound: Value | None = None
    id: Value | None = None
    delay: Value | None = None
    apply_latency: Condition | None = None
    fade_in: Value | None = None
    lane: Value | None = None
    volume: Value | None = None
    pitch: Value | None = None


class SoundCancelEvent(BaseEvent, type='SoundCancel'):
    '''
    Attributes:
        ids: List of sound effect IDs to cancel
    '''
    
    ids: JList[Value]


class AnimateEvent(BaseEvent, type='Animate'):
    '''
    Attributes:
        id: ID of the entity to animate
        type: Name of the animation type to play
    '''
    
    id: Value
    type: AnimationType


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
    
    id: Value
    attribute: SpriteAttribute
    operator: BinaryOperator | None = None
    x: Value | None = None
    y: Value | None = None
    z: Value | None = None
    w: Value | None = None


class SpriteStringEvent(BaseEvent, type='SpriteString'):
    '''
    Attributes:
        id: ID of the sprite to affect
        attribute: Attribute to modify
        text: String value to assign
    '''
    
    id: Value
    attribute: SpriteStringAttribute
    text: String


class GraphicCreateEvent(BaseEvent, type='GraphicCreate'):
    '''
    Attributes:
        id: Reference ID of the graphic to create. Distinct from visual IDs. Must be unique
        parent: Visual ID to attach the graphic to. If nil, attaches to the stage root
        type: Subtype of the graphic object to instantiate
    '''
    
    id: Value
    parent: Value | None = None
    type: GraphicType | None = None


class GraphicDestroyEvent(BaseEvent, type='GraphicDestroy'):
    '''
    Attributes:
        id: Reference ID of the graphic to destroy
    '''
    
    id: Value


class PlayerHealthEvent(BaseEvent, type='PlayerHealth'):
    '''
    Attributes:
        id: Entity ID inflicting the hit/heal for stat tracking (in case of a player death)
        diff: Amount of health to add (positive) or remove (negative)
    '''
    
    id: Value
    diff: Value


class ScoreEvent(BaseEvent, type='Score'):
    '''
    Attributes:
        type: Type of score incrementation to perform
        amount: For 'Extra' type scores, exact amount of score to grant to the player
    '''
    
    type: ScoreType
    amount: int | None = None


class ComboAddEvent(BaseEvent, type='ComboAdd'):
    '''
    Attributes:
    '''


class ComboDropEvent(BaseEvent, type='ComboDrop'):
    '''
    Attributes:
    '''


class StatEvent(BaseEvent, type='Stat'):
    '''
    Attributes:
        type: Type name of the entity for which stats should be tracked
        stat: Stat type to increment
        amount: Amount to change stat by (if nil, 1)
    '''
    
    type: String
    stat: Statistic
    amount: int | None = None


class SystemEvent(BaseEvent, type='System'):
    '''
    Attributes:
        attribute: System attribute to assign
        value: Value to assign to the attribute
    '''
    
    attribute: SystemAttribute
    value: Value


class FinishLevelEvent(BaseEvent, type='FinishLevel'):
    '''
    Attributes:
        win: If true, the completion counts as a victory
    '''
    
    win: Condition


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
    
    id: Value
    mask: ButtonMask
    rating_id: int
    offset: Value | None = None
    release_offset: Value | None = None
    priority: Value | None = None
    force_split: Condition | None = None
    on_hit: BaseEvent | None = None
    on_release: BaseEvent | None = None
    on_miss: BaseEvent | None = None


class InputCloseEvent(BaseEvent, type='InputClose'):
    '''
    Attributes:
        id: Unique ID of the input window to close
    '''
    
    id: Value


class StartStreamEvent(BaseEvent, type='StartStream'):
    '''
    Attributes:
        id: ID of the event stream to start
        ref_id: Reference ID of the event stream to start (for later stopping)
        immediate: If true, immediately processes the stream's events prior to resuming execution
        locals: Optional list of local variables to initialize the stream with
    '''
    
    id: Value
    ref_id: Value
    immediate: Condition
    locals: JList[Value] | None = None
    
    @override
    def to_json_obj(self):
        dict = self.to_dict()
        ref_id = dict.pop('refId')
        dict['refID'] = ref_id
        return dict


class StopStreamEvent(BaseEvent, type='StopStream'):
    '''
    Attributes:
        ref_id: Reference ID of the event stream to stop (or nil to stop own stream)
    '''
    
    ref_id: Value | None = None
    
    @override
    def to_json_obj(self):
        dict = self.to_dict()
        if 'refId' in dict:
            ref_id = dict.pop('refId')
            dict['refID'] = ref_id
        return dict

class IfEvent(BaseEvent, type='If'):
    '''
    Attributes:
        condition: Condition to check
        yes: Event to execute if condition is met
        no: Event to execute if condition is not met
    '''
    
    condition: Condition
    yes: BaseEvent | None
    no: BaseEvent | None


class JumpEvent(BaseEvent, type='Jump'):
    '''
    Attributes:
        target: Instruction index to jump to
    '''
    
    target: Value


class WaitEvent(BaseEvent, type='Wait'):
    '''
    Attributes:
        condition: Waits until this condition is true. If nil, waits for one tick instead
    '''
    
    condition: Condition | None = None


class SetArrayEvent(BaseEvent, type='SetArray'):
    '''
    Attributes:
        name: Name of the array to modify, or nil for the stream's local variables array
        index: Array index to modify, or nil for resizing the array
        value: Value to write to the array
    '''
    
    name: String | None = None
    index: Value | None = None
    value: Value | None = None


class SetArrayStringEvent(BaseEvent, type='SetArrayString'):
    '''
    Attributes:
        name: Name of the array to modify, or nil for the stream's local variables array
        string: String to convert to UTF-32 and write to the array
    '''
    
    name: String | None = None
    string: String | None = None


class SetVariableEvent(BaseEvent, type='SetVariable'):
    '''
    Attributes:
        name: Name of the variable to assign
        value: Value to write to the variable
    '''
    
    name: String
    value: Value


class LogEvent(BaseEvent, type='Log'):
    '''
    Attributes:
        text: Text to write to the log (use {0}, {1}, etc. for placeholders)
        args: Optional list of values to populate placeholders
    '''
    
    text: String


class TimedEvent(JObj):
    t: float
    event: BaseEvent
    
    @override
    def to_json_obj(self):
        return {
            't': self.t,
            **self.event.to_dict()
        }
