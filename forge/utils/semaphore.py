# -*- coding: utf-8 -*-

"""Delayed Bounded Semaphore for HTTP Connections"""

from asyncio import BoundedSemaphore, sleep
from collections import deque
from datetime import datetime

from inspect import iscoroutinefunction
from time import sleep as tsleep


class HTTPSemaphore(BoundedSemaphore):
    def __init__(
        self, value: int = 10, delay: float = 0.06, size: int = 10, **kwargs
    ) -> None:
        self.delay = delay
        self.size = size
        self.acquisitions = deque(maxlen=self.size)
        super().__init__(value, **kwargs)

    def _delay(self):
        if len(self.acquisitions) == self.size:
            first = self.acquisitions.popleft()
            last = self.acquisitions[-1]

            delta = (last - first).total_seconds()
            if delta < 1.0:
                return True
            else:
                return False
        else:
            return False

    def delay(func):
        async def inner_coro(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            while self._delay():
                print("I have been delayed")
                await sleep(self.delay)
            self.acquisitions.append(datetime.now())
            return result

        def inner_func(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            while self._delay():
                print("I have been delayed")
                tsleep(self.delay)
            self.acquisitions.append(datetime.now())
            return result

        inner = inner_coro if iscoroutinefunction(func) else inner_func

        return inner

    acquire = delay(BoundedSemaphore.acquire)
