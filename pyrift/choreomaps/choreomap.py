from pyrift.jobj import JObj

from .nodes import RatingDefinition, Sound, Stream


class Choreomap(JObj):
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
