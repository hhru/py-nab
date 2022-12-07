from .common import json_serialize


def kafka_json_serialize(value) -> bytes:
    return json_serialize(value).encode()
