from datetime import datetime
import json
from functools import wraps
from sqlalchemy.orm import class_mapper

def serialize_sqlalchemy_obj(obj):
    data = {}
    for column in class_mapper(obj.__class__).columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            data[column.name] = value.isoformat()
        else:
            data[column.name] = value
    return data

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def redis_cache(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        cache_key = f"{func.__name__}"
        cached_result = self.redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        result = func(self, *args, **kwargs)
        serialized_result = json.dumps([serialize_sqlalchemy_obj(store) for store in result], cls=DateTimeEncoder)
        self.redis_client.set(cache_key, serialized_result)
        
        return result
    return wrapper
