import logging
import time
from enum import Enum
from functools import wraps
from typing import Any


log = logging.getLogger(__name__)


class CacheType(Enum):
    GLOBAL = "global"          # один кэш на всех
    UNIVERSITY = "university"  # по host
    LOGIN = "login"            # по host + login


_cache: dict[str, tuple[Any, float]] = {}


def _make_key(cache_type: CacheType, func_name: str, self_obj: Any, args: tuple, kwargs: dict) -> str:
    args_part = ":".join(str(a) for a in args) if args else ""
    kwargs_part = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items())) if kwargs else ""
    
    match cache_type:
        case CacheType.GLOBAL:
            return f"global:{func_name}:{args_part}:{kwargs_part}"
        case CacheType.UNIVERSITY:
            return f"uni:{self_obj.base_url}:{func_name}:{args_part}:{kwargs_part}"
        case CacheType.LOGIN:
            return f"login:{self_obj.base_url}:{self_obj.login}:{self_obj.password}:{func_name}:{args_part}:{kwargs_part}"
        

def cache(cache_type: CacheType, ttl: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            key = _make_key(cache_type, func.__name__, self, args, kwargs)
            now = time.monotonic()

            if key in _cache:
                value, expires_at = _cache[key]
                if now < expires_at:
                    remaining = round(expires_at - now)
                    log.debug(f"[CACHE HIT] {key} (ttl left: {remaining}s)")
                    return value
                else:
                    log.debug(f"[CACHE EXPIRED] {key}")
                    del _cache[key]

            log.debug(f"[CACHE MISS] {key} — fetching...")
            result = await func(self, *args, **kwargs)
            _cache[key] = (result, now + ttl)
            log.debug(f"[CACHE SET] {key} (ttl: {ttl}s)")
            return result

        return wrapper
    return decorator


def invalidate_cache(cache_type: CacheType, host: str = "", login: str = ""):
    prefix = {
        CacheType.GLOBAL: "global:",
        CacheType.UNIVERSITY: f"uni:https://{host}/rest:",
        CacheType.LOGIN: f"login:https://{host}/rest:{login}:",
    }[cache_type]

    keys_to_delete = [k for k in _cache if k.startswith(prefix)]
    for k in keys_to_delete:
        del _cache[k]

    log.info(f"[CACHE INVALIDATED] prefix={prefix!r} ({len(keys_to_delete)} keys)")