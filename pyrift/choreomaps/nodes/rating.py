from dataclasses import dataclass

from .enum import InputRating, InputTiming


@dataclass(frozen=True)
class RatingStep:
    '''
    Attributes:
        threshold: Relative time offset since the start of the input window
        base_score: Score for this rating step
        bonus_score: Additional score for this rating step (unaffected by combo or vibe power)
        rating: Visual rating for this input window
        timing: E/L indicator for this input window
    '''
    
    threshold: float
    base_score: float
    bonus_score: float
    rating: InputRating
    timing: InputTiming


@dataclass(frozen=True)
class RatingDefinition:
    '''
    Attributes:
        steps: List of rating steps
    '''
    
    steps: tuple[RatingStep, ...]
