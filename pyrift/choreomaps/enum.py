from enum import Enum


class TimingMode(Enum):
    SONG_START = 'SongStart'
    WINDOW_CENTER = 'WindowCenter'
    WINDOW_START = 'WindowStart'
    WINDOW_END = 'WindowEnd'
    STREAM_START = 'StreamStart'

class ButtonMask(Enum):
    NONE = 0
    LEFT = 1
    CENTER = 2
    RIGHT = 3
    MULTI = 4
    VIBE = 5

class Statistic(Enum):
    HITS = 'Hits'
    KILLS = 'Kills'
    DAMAGE_TAKEN = 'DamageTaken'
    DEATHS_TAKEN = 'DeathsTaken'

class ScoreType(Enum):
    RATING = 'Rating'
    HOLD = 'Hold'
    EXTRA_FLAT = 'ExtraFlat'
    EXTRA_COMBO = 'ExtraCombo'

class SoundPrediction(Enum):
    HIT = 'Hit'
    MISS = 'Miss'

class MoveLerp(Enum):
    NORMAL = 'Normal'
    INSTANT = 'Instant'

class Status(Enum):
    BURNING = 'Burning'
    SHOCKED = 'Shocked'
    MIRRORED = 'Mirrored'
    SHIELDED = 'Shielded'
    FROZEN = 'Frozen'
    MYSTERIOUS = 'Mysterious'
    POOFING = 'Poofing'
    VIBING = 'Vibing'
    DEBUG_LOCKED = 'DebugLocked'

class AnimationType(Enum):
    MOVE = 'Move'
    MOVE_SHIELD = 'MoveShield'
    MOVE_HEADLESS = 'MoveHeadless'
    ATTACK = 'Attack'
    ATTACK_SHIELD = 'AttackShield'
    ATTACK_HEADLESS = 'AttackHeadless'
    ATTACK_PREPARE = 'AttackPrepare'
    ATTACK_FOLLOW_UP = 'AttackFollowUp'
    HIT = 'Hit'
    HIT_SHIELD = 'HitShield'
    DEATH = 'Death'
    DEATH_HEADLESS = 'DeathHeadless'
    WRAP_LEAVE_LEFT = 'WrapLeaveLeft'
    WRAP_LEAVE_RIGHT = 'WrapLeaveRight'
    WRAP_ENTER_LEFT = 'WrapEnterLeft'
    WRAP_ENTER_RIGHT = 'WrapEnterRight'

class EntityAttribute(Enum):
    TYPE = 'Type'
    HEALTH = 'Health'
    SHIELD = 'Shield'
    GRID_X = 'GridX'
    GRID_Y = 'GridY'
    WORLD_X = 'WorldX'
    WORLD_Y = 'WorldY'
    WORLD_Z = 'WorldZ'
    FACING = 'Facing'
    TINT_COLOR = 'TintColor'
    SPRITE_OVERRIDE = 'SpriteOverride'

class EntityPredicate(Enum):
    EXISTS = 'Exists'
    DYING = 'Dying'

class SystemAttribute(Enum):
    INSTRUCTION_INDEX = 'InstructionIndex'
    SONG_TIME = 'SongTime'
    STREAM_TIME = 'StreamTime'
    BEAT_DURATION = 'BeatDuration'
    AUDIO_LATENCY = 'AudioLatency'
    VIDEO_LATENCY = 'VideoLatency'
    DIFFICULTY = 'Difficulty'
    INPUT_BUTTON = 'InputButton'
    INPUT_RATING = 'InputRating'
    INPUT_TIMING = 'InputTiming'
    INPUT_BASE_SCORE = 'InputBaseScore'
    INPUT_BONUS_SCORE = 'InputBonusScore'
    HEALTH = 'Health'
    SCORE = 'Score'
    COMBO = 'Combo'
    MULTIPLIER = 'Multiplier'
    VIBE_METER = 'VibeMeter'

class SystemPredicate(Enum):
    FAST_FORWARD_ACTIVE = 'FastForwardActive'
    UP_DOWN_INVERTED = 'UpDownInverted'
    PRACTICE = 'Practice'
    MODE_REMIX = 'ModeRemix'
    MODE_REMIX_SEEDED = 'ModeRemixSeeded'
    MODIFIER_GLASS_GUITAR = 'ModifierGlassGuitar'
    MODIFIER_PERFECTIONIST = 'ModifierPerfectionist'
    MODIFIER_ENIGMA = 'ModifierEnigma'
    MODIFIER_GLOOM = 'ModifierGloom'
    MODIFIER_NIGHTMARE = 'ModifierNightmare'
    MODIFIER_CODA = 'ModifierCoda'
    MODIFIER_PURIST = 'ModifierPurist'
    MODIFIER_BAT_BANE = 'ModifierBatBane'
    MODIFIER_SLIME_BANE = 'ModifierSlimeBane'
    MODIFIER_HARPY_BANE = 'ModifierHarpyBane'
    MODIFIER_BLADEMASTER_BANE = 'ModifierBlademasterBane'
    MODIFIER_SKELETON_BANE = 'ModifierSkeletonBane'
    MODIFIER_BOSS_DOUBLE_DAMAGE = 'ModifierBossDoubleDamage'
    MODIFIER_DOUBLE_PLAYER_HEALTH = 'ModifierDoublePlayerHealth'
    MODIFIER_INVINCIBILITY_BEATS = 'ModifierInvincibilityBeats'
    MODIFIER_EXTRA_HEALTH_ITEMS = 'ModifierExtraHealthItems'
    MODIFIER_GOLDEN_LUTE = 'ModifierGoldenLute'

class ComparisonMode(Enum):
    EQUAL = 'Equal'
    NOT_EQUAL = 'NotEqual'
    LESS = 'Less'
    LESS_EQUAL = 'LessEqual'
    GREATER = 'Greater'
    GREATER_EQUAL = 'GreaterEqual'

class BinaryOperator(Enum):
    ADD = 'Add'
    SUBTRACT = 'Subtract'
    MULTIPLY = 'Multiply'
    DIVIDE = 'Divide'
    MOD = 'Mod'
    POWER = 'Power'
    MAX = 'Max'
    MIN = 'Min'
    RANDOM_INT = 'RandomInt'
    RANDOM_FLOAT = 'RandomFloat'
    OR = 'Or'
    AND = 'And'
    XOR = 'Xor'
    L_SHIFT = 'LShift'
    R_SHIFT = 'RShift'

class UnaryOperator(Enum):
    ABS = 'Abs'
    SIGN = 'Sign'
    FLOOR = 'Floor'
    CEIL = 'Ceil'
    SQRT = 'Sqrt'
    SIN = 'Sin'
    COS = 'Cos'
    TAN = 'Tan'
    ASIN = 'Asin'
    ACOS = 'Acos'
    ATAN = 'Atan'
    LOG = 'Log'
    EXP = 'Exp'
    NOT = 'Not'

class GraphicType(Enum):
    CANVAS = 'Canvas'
    CANVAS_MASKABLE = 'CanvasMaskable'
    SPRITE = 'Sprite'

class SpriteAttribute(Enum):
    WORLD_POSITION = 'WorldPosition'
    POSITION = 'Position'
    SCALE = 'Scale'
    ROTATION = 'Rotation'
    COLOR = 'Color'
    TEXTURE = 'Texture'
    SORTING_LAYER = 'SortingLayer'

class VisualType(Enum):
    STAGE_ROOT = 'StageRoot'
    GRID_ROOT = 'GridRoot'
    GRID_TILE = 'GridTile'
    GRID_TILE_STRING = 'GridTileString'
    GRID_TILE_ARROW = 'GridTileArrow'
    PORTRAIT_PARENT = 'PortraitParent'
    PORTRAIT_ROOT = 'PortraitRoot'
    PORTRAIT_BACKGROUND = 'PortraitBackground'
    PORTRAIT_MASK = 'PortraitMask'
    PORTRAIT_SPRITE = 'PortraitSprite'
    ENTITY_ROOT = 'EntityRoot'
    ENTITY_SCALE_POINT = 'EntityScalePoint'
    ENTITY_STATUS_POINT = 'EntityStatusPoint'
    ENTITY_SPRITE = 'EntitySprite'
    ENTITY_SHADOW = 'EntityShadow'
    ENTITY_HEALTH_INDICATOR = 'EntityHealthIndicator'
    HUD_ROOT = 'HudRoot'
    HUD_SONG_INFO_ROOT = 'HudSongInfoRoot'
    HUD_SONG_INFO_TRACK_NAME = 'HudSongInfoTrackName'
    HUD_SONG_INFO_TRACK_ARTIST = 'HudSongInfoTrackArtist'
    HUD_SONG_INFO_DIFFICULTY = 'HudSongInfoDifficulty'
    HUD_SCOREBOARD_ROOT = 'HudScoreboardRoot'
    HUD_SCOREBOARD_COMBO_BACKGROUND = 'HudScoreboardComboBackground'
    HUD_SCOREBOARD_COMBO_VALUE = 'HudScoreboardComboValue'
    HUD_SCOREBOARD_MULTIPLIER_BACKGROUND = 'HudScoreboardMultiplierBackground'
    HUD_SCOREBOARD_MULTIPLIER_VALUE = 'HudScoreboardMultiplierValue'
    HUD_SCOREBOARD_SCORE_BACKGROUND = 'HudScoreboardScoreBackground'
    HUD_SCOREBOARD_SCORE_VALUE = 'HudScoreboardScoreValue'
    HUD_PLAYER_ROOT = 'HudPlayerRoot'
    HUD_PLAYER_BACKGROUND = 'HudPlayerBackground'
    HUD_PLAYER_HEART = 'HudPlayerHeart'
    HUD_PLAYER_HEART_FILL = 'HudPlayerHeartFill'
    HUD_PLAYER_HEART_OUTLINE = 'HudPlayerHeartOutline'
    HUD_PLAYER_HEALTH_BAR = 'HudPlayerHealthBar'
    HUD_PLAYER_HEALTH_VALUE = 'HudPlayerHealthValue'
    HUD_PLAYER_HEALTH_SLASH = 'HudPlayerHealthSlash'
    HUD_PLAYER_HEALTH_MAX = 'HudPlayerHealthMax'
    HUD_PLAYER_HEALTH_MAX_OUTLINE = 'HudPlayerHealthMaxOutline'
    HUD_PLAYER_GUITAR = 'HudPlayerGuitar'
    HUD_PLAYER_VIBE_BOLT_A = 'HudPlayerVibeBoltA'
    HUD_PLAYER_VIBE_BOLT_B = 'HudPlayerVibeBoltB'
    GRAPHIC = 'Graphic'
    GRAPHIC_MASK = 'GraphicMask'

class InputRating(Enum):
    MISS = 'Miss'
    OK = 'Ok'
    GOOD = 'Good'
    GREAT = 'Great'
    PERFECT = 'Perfect'

class InputTiming(Enum):
    EARLY = 'Early'
    FLAWLESS = 'TrueFlawless'
    LATE = 'Late'
