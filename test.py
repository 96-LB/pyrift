import json

import test_choreomap
from pyrift.choreomaps import compile

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
            "choreomap": compile(test_choreomap)
        },
        f,
        default=lambda x: x.to_json_obj() if hasattr(x, 'to_json_obj') else str(x.value),
        indent=4
    )
