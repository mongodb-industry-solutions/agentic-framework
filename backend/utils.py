from bson import ObjectId
from typing import Any

def convert_objectids(item: Any) -> Any:
    if isinstance(item, list):
        return [convert_objectids(i) for i in item]
    elif isinstance(item, dict):
        return {k: convert_objectids(v) for k, v in item.items()}
    elif isinstance(item, ObjectId):
        return str(item)
    else:
        return item