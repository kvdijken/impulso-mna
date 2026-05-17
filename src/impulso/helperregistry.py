from __future__ import annotations
from typing import Dict, List, Protocol, Type, TYPE_CHECKING
from collections import defaultdict

from .components.component import Context, Stamper

if TYPE_CHECKING:
    from .circuit import Circuit


class Helper(Protocol):
    def prepare(self,
                circuit: Circuit,
                ctx: Context):
        ...


class StampingHelper(Helper, Stamper):
        ...


class Factory(Protocol):
    def creates(self) -> Type[Helper]:
        ...

    def create_helper(self,
                      circuit: Circuit,
                      ctx: Context) -> Helper:
        ...


class Registry:
    def __init__(self):
        self._factories: Dict[Type[Helper],           # type of Contributor
                             List[                        # all providers for that type
                                  tuple[str,              # name of the provider
                                        Factory          # the provider itself
                                        ]]] = defaultdict(list)

    def register_factory(self,
                         name: str,
                         factory: Factory):
        creates = factory.creates()
        self._factories[creates].append((name, factory))

    def factories(self,
                  cls: Type[Helper]
                  ) -> List[tuple[str, Factory]]:
        return self._factories[cls]

registry = Registry()



