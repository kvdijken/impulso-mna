from typing import Optional

from .component import Component, Context, Stamper


class Resistor(Component, Stamper):
    """Resistor component."""

    def __init__(self, resistance: float, id: Optional[str] = None):
        if resistance < 0:
            raise ValueError(f"Resistance must be non-negative, got {resistance}")
        super().__init__(id)
        self.resistance = resistance
        self.g = 1.0 / resistance

    def admittance(self, s: Optional[complex] = None) -> complex:
        return self.g

    def stamp(self, ctx: Context):
        i, j = ctx.idx_query_fn(self)
        if i is not None:
            ctx.Y[i, i] += self.g
        if j is not None:
            ctx.Y[j, j] += self.g
        if i is not None and j is not None:
            ctx.Y[i, j] -= self.g
            ctx.Y[j, i] -= self.g


    def current(self, ctx: Context) -> complex:
        i, j = ctx.idx_query_fn(self)
        if i is None:
            vi = 0
        else:
            vi = ctx.x[i]
        if j is None:
            vj = 0
        else:
            vj = ctx.x[j]
        return (vi - vj) * self.g

