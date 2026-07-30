import datetime
import json
from postgrest.utils import sanitize_param

data = {"date_of_birth": datetime.date(2020, 1, 1)}
try:
    print("Trying to serialize data")
    json.dumps(data)
except Exception as e:
    print("Failed standard json:", e)

import httpx
try:
    req = httpx.Request("POST", "http://a", json=data)
    print("httpx json succeeds")
except Exception as e:
    print("httpx failed:", e)
