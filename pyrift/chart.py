from dataclasses import dataclass

from .difficulty import Difficulty
from .event import Event
from .typeddicts import ChartDict, DifficultyInfoDict


@dataclass
class Chart:
    difficulty: Difficulty
    
    intensity: float
    bpm: float
    beat_count: int
    final_input_beat_override: int
    
    subdivisions: int
    coal_speed: int
    countdown: int
    offset: float
    
    events: list[Event]
    
    def to_info_dict(self, name: str, index: int) -> DifficultyInfoDict:
        return {
            'BeatCount': self.beat_count,
            'BeatmapFileName': f'{name}_{index}.json',
            'BeatsPerMinute': self.bpm,
            'DifficultyLabel': self.difficulty.value,
            'FinalInputBeatOverride': self.final_input_beat_override,
            'Intensity': self.intensity
        }
    
    def to_chart_dict(self, name: str) -> ChartDict:
        return {
            'beatDivisions': self.subdivisions,
            'bpm': self.bpm,
            'cameraZoomLevel': 0,
            'coalTrapSpeedUpFactorOverride': self.coal_speed,
            'countdownBpm': self.bpm,
            'countdownTicks': self.countdown,
            'defaultBossStance': 0,
            'events': [e.to_dict() for e in self.events],
            'inputMappingOverrideJson': '',
            'name': name,
            'playbackOffset': -4,
            'playbackOffsetTime': self.offset,
            'shouldSetBossStanceOnBeatmapStart': False
        }
            
