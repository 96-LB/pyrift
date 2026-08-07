from dataclasses import dataclass, fields

from util import snake_to_camel

from .nodes import RatingDefinition, Sound, Stream


@dataclass(frozen=True)
class Choreomap:
    '''
    Attributes:
        streams: List of all streams contained in the Choreomap
        input_rating_definitions: List of input rating definitions
        main_id: Main stream ID for this Choreomap
        miss_id: Miss stream ID for this Choreomap
        sounds: List of sound effects
    '''
    
    streams: tuple[Stream, ...]
    input_rating_definitions: tuple[RatingDefinition, ...]
    main_id: int
    miss_id: int | None = None
    sounds: tuple[Sound, ...] = ()
    
    def to_dict(self):
        field_values = {snake_to_camel(f.name): getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}
        return field_values
