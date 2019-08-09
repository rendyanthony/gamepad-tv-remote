import time
import types

class Tasks(object):
    def __init__(self):
        self._tasks = []

    def _periodic(self, period, func, *args, **kwargs):
        next_t = 0
        while True:
            now = time.time()
            if now >= next_t:
                func(*args, **kwargs)
                next_t = now + period
            yield
    
    def _always(self, func, *args, **kwargs):
        while True:
            yield func(*args, **kwargs)

    def add(self, func):
        if not isinstance(func, types.GeneratorType):
            func = self._always(func)
        self._tasks.append(func)

    def add_periodic(self, period, func):
        self._tasks.append(
            self._periodic(period, func))

    def do(self):
        for task in self._tasks:
            next(task)