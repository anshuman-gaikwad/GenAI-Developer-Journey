
"""Small in-memory cache for approved general consumer-law questions."""

import time
from collections import OrderedDict
from copy import deepcopy
from threading import Lock

CACHE_TTL_SECONDS = 300
CACHE_MAX_ENTRIES = 100

# Only these general, non-personal questions are eligible for caching.
CACHEABLE_QUESTIONS = frozenset(
    {
        "what is an unfair trade practice?",
        "what are consumer rights?",
        "what is a defective product?",
        "what is deficiency in service?",
    }
)

_cache = OrderedDict()
_lock = Lock()


def normalize_question(question):
    """Normalize whitespace and capitalization for cache lookup."""
    return " ".join(question.strip().lower().split())


def is_cacheable_question(question):
    """Allow caching only for explicitly approved general questions."""
    return normalize_question(question) in CACHEABLE_QUESTIONS


def get_cached_response(key):
    """Return an independent copy of an unexpired cached response."""
    with _lock:
        entry = _cache.get(key)

        if entry is None:
            return None

        expires_at, response = entry

        if time.monotonic() >= expires_at:
            del _cache[key]
            return None

        _cache.move_to_end(key)
        return deepcopy(response)


def set_cached_response(key, response):
    """Store an independent response copy for a limited time."""
    with _lock:
        expires_at = time.monotonic() + CACHE_TTL_SECONDS

        _cache[key] = (expires_at, deepcopy(response))
        _cache.move_to_end(key)

        while len(_cache) > CACHE_MAX_ENTRIES:
            _cache.popitem(last=False)


def clear_cache():
    """Clear cache entries, primarily for automated tests."""
    with _lock:
        _cache.clear()
