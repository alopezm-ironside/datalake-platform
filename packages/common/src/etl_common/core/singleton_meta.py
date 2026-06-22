# Thread-safe singleton, adapted from https://refactoring.guru/design-patterns/singleton/python/example#example-1
from threading import Lock


class SingletonMeta(type):
    """A thread-safe implementation of Singleton."""

    _instances: dict = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        # Lock guards the first-access race: the first thread to acquire the
        # lock creates the instance; subsequent threads see it already set.
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]
