from dataclasses import dataclass


@dataclass(frozen=True)
class Sound:
    '''
    Attributes:
        id: FMOD sound event ID (prefixed with "$fmod$") for built-in sound events
        events: Relative audio file path for custom sound files
        timing_mode: FMOD audio bus name for custom sound files
    '''
    fmod: str | None = None
    path: str | None = None
    bus: str | None = None
