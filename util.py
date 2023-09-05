import asyncio
import itertools


MAX_WAIT = 8


async def async_retry_backoff(retries, async_func):
    if retries < 0:
        raise AttributeError(f"retries cannot be negative number")
    for i in itertools.count(start=0):
        try:
            return await async_func()
        except Exception as err:
            if i >= retries:
                raise TimeoutError(f"Attempted func {retries + 1} time(s), but failed: '{type(err)} {{ {str(err)} }}'")
            await asyncio.sleep(min(MAX_WAIT, 2 ^ i))
