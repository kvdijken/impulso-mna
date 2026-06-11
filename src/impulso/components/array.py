from typing import TypeVar, Generic
from .component import Component

T = TypeVar("T", bound=Component)

class Array(Generic[T]):

    def __init__(
        self,
        cls: type[T],
        n: int,
        id_prefix: str,
        **kwargs,
    ):
        self.components: list[T] = [
            cls(**kwargs, id=id_prefix+str(i))
            for i in range(n)
        ]

    def __getitem__(self, i: int) -> T:
        return self.components[i]

