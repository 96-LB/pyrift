from .condition import AndCondition, CompareCondition, ConstantCondition, EntityCondition, NotCondition, OrCondition, SystemCondition
from .event import AnimateEvent, ComboAddEvent, ComboDropEvent, DespawnEvent, EntityAttributeEvent, FinishLevelEvent, GraphicCreateEvent, GraphicDestroyEvent, HitVfxEvent, IfEvent, InputCloseEvent, InputOpenEvent, JumpEvent, LogEvent, MoveEvent, PlayerHealthEvent, ScoreEvent, SetArrayEvent, SetVariableEvent, SoundCancelEvent, SoundEvent, SpawnEvent, SpriteEvent, StartStreamEvent, StatEvent, StatusAddEvent, StatusRemoveEvent, StopStreamEvent, SystemEvent, WaitEvent
from .value import ArrayValue, ConstantValue, EntityValue, IfValue, MathValue, SpriteAttributeValue, SpriteFindIDValue, SpriteIDValue, SystemValue, UnaryValue, VariableValue


type Condition = ConstantCondition | AndCondition | OrCondition | NotCondition | CompareCondition | EntityCondition | SystemCondition
type Event = SpawnEvent | DespawnEvent | EntityAttributeEvent | MoveEvent | StatusAddEvent | StatusRemoveEvent | HitVfxEvent | SoundEvent | SoundCancelEvent | AnimateEvent | SpriteEvent | GraphicCreateEvent | GraphicDestroyEvent | PlayerHealthEvent | ScoreEvent | ComboAddEvent | ComboDropEvent | StatEvent | SystemEvent | FinishLevelEvent | InputOpenEvent | InputCloseEvent | StartStreamEvent | StopStreamEvent | IfEvent | JumpEvent | WaitEvent | SetArrayEvent | SetVariableEvent | LogEvent
type Value = ConstantValue | MathValue | UnaryValue | IfValue | VariableValue | ArrayValue | EntityValue | SystemValue | SpriteIDValue | SpriteFindIDValue | SpriteAttributeValue
