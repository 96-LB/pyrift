import json

import test_choreomap
from pyrift.choreomaps import build

with open('test.json', 'w') as f:
    json.dump(
        {
            "bpm": 200,
            "beatDivisions": 2,
            "name": "_test2_",
            "coalTrapSpeedUpFactorOverride": 2,
            "countdownTicks": 4,
            "countdownBpm": 200,
            "playbackOffset": -4,
            "playbackOffsetTime": 0,
            "name": "_test2_",
            "choreomap": build(test_choreomap)
        },
        f,
        default=lambda x: x.to_obj() if hasattr(x, 'to_obj') else x.to_dict() if hasattr(x, 'to_dict') else str(x.value),
        indent=4
    )
