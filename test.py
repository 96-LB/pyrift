import json

import test_choreomap
from pyrift.choreomaps import build

with open('test.json', 'w') as f:
    json.dump(
        build(test_choreomap),
        f,
        default=lambda x: x.to_obj() if hasattr(x, 'to_obj') else x.to_dict() if hasattr(x, 'to_dict') else str(x.value),
        indent=4
    )