from dataclasses import dataclass

from .chart import Chart
from .typeddicts import ChartInfoDict


@dataclass
class ChartInfo:
    cover_file: str
    audio_file: str
    video_file: str
    
    title: str
    artist: str
    subtitle: str
    creator: str
    
    track_length: str
    bpm: float
    
    counterpart: str
    
    difficulties: list[Chart]
    
    @property
    def beat_count(self) -> int:
        return max((d.beat_count for d in self.difficulties), default=0)
    
    def to_dict(self, chart_name: str) -> ChartInfoDict:
        return {
            'AlbumArtFileName': self.cover_file,
            'ArtistName': self.artist,
            'AudioFileName': self.audio_file,
            'BeatCount': self.beat_count,
            'BeatsPerMinute': self.bpm,
            'Counterpart': self.counterpart,
            'DifficultyInformation': [d.to_info_dict(chart_name, i + 1) for i, d in enumerate(self.difficulties)],
            'StageCreatorName': self.creator,
            'TrackLength': self.track_length,
            'TrackName': self.title,
            'TrackSubtitle': self.subtitle,
            'Version': 1,
            'VideoFileName': self.video_file
        }
