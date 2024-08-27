import json
from functools import wraps

def redis_cache(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        cache_key = f"{func.__name__}"
        cached_result = self.redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        result = func(self, *args, **kwargs)
        serialized_result = json.dumps([store.dict() for store in result])
        self.redis_client.set(cache_key, serialized_result)
        
        return result
    return wrapper
