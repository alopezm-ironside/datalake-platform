from typing import Type, TypeVar

T = TypeVar("T")


class DependencyContainer:
    _registry: dict = {}

    @classmethod
    def register(cls, key: Type[T], instance: T) -> None:
        cls._registry[key] = instance

    @classmethod
    def resolve(cls, key: Type[T]) -> T:
        instance = cls._registry.get(key)
        if instance is None:
            raise RuntimeError(f"{key.__name__} was not registered in the container.")
        return instance
