from dataclasses import dataclass

from ..event import Event

@dataclass
class SpawnEnemyEvent(Event, type='SpawnEnemy'):
    