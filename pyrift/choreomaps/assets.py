from ..jobj import JObj


class Sprite(JObj):
    path: str
    id: int | None = None
    pixels_per_unit: float = 100
    pivot_x: float = 0.5
    pivot_y: float = 0.5
    extrude: float = 1

class Assets(JObj):
    sprites: dict[str, Sprite]
