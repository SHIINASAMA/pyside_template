import asyncio
import sys
from functools import partial
from typing import Callable, Any

if sys.version_info >= (3, 9):
    to_thread = asyncio.to_thread
else:
    async def to_thread(func: Callable, /, *args, **kwargs) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))