import json
from datetime import datetime


def date_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Cannot serialize {obj}")


def json_serialize(value: dict) -> str:
    return json.dumps(value, default=date_serializer)
