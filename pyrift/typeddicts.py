from typing import Literal, TypedDict


class DifficultyInfoDict(TypedDict):
    BeatCount: int
    BeatmapFileName: str
    BeatsPerMinute: float
    DifficultyLabel: Literal['Easy', 'Medium', 'Hard', 'Impossible']
    FinalInputBeatOverride: int
    Intensity: float


class ChartInfoDict(TypedDict):
    AlbumArtFileName: str
    ArtistName: str
    AudioFileName: str
    BeatCount: int
    BeatsPerMinute: float
    Counterpart: str
    DifficultyInformation: list[DifficultyInfoDict]
    StageCreatorName: str
    TrackLength: str
    TrackName: str
    TrackSubtitle: str
    Version: int
    VideoFileName: str


class EventDataPairDict(TypedDict):
    _eventDataKey: str
    _eventDataValue: str


class EventDict(TypedDict):
    clipin: int
    dataPairs: list[EventDataPairDict]
    endBeatNumber: float
    group: int
    startBeatNumber: float
    track: Literal[1, 2, 3]
    type: str


class ChartDict(TypedDict):
    beatDivisions: int
    bpm: float
    cameraZoomLevel: int
    coalTrapSpeedUpFactorOverride: int
    countdownBpm: float
    countdownTicks: int
    defaultBossStance: int
    events: list[EventDict]
    inputMappingOverrideJson: str
    name: str
    playbackOffset: int
    playbackOffsetTime: float
    shouldSetBossStanceOnBeatmapStart: bool
