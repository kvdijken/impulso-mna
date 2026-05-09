from typing import Dict, List, Tuple, Optional, Type, Any

from .component import Component, Context


class Resistor(Component):
    """Resistor component."""

    def __init__(self, resistance: float, id: Optional[str] = None):
        if resistance < 0:
            raise ValueError(f"Resistance must be non-negative, got {resistance}")
        super().__init__(id)
        self.resistance = resistance

    def admittance(self, s: Optional[complex] = None) -> complex:
        return 1 / self.resistance

    def augments(self):
        return False

    def stamp(self, ctx: Context):
        g = 1.0 / self.resistance
        idx = ctx.idx_query_fn(self)
        i, j = idx
        if i is not None and j is not None:
            ctx.Y[i, i] += g
            ctx.Y[j, j] += g
            ctx.Y[i, j] -= g
            ctx.Y[j, i] -= g
        elif i is not None:
            ctx.Y[i, i] += g
        elif j is not None:
            ctx.Y[j, j] += g


    def current(self, ctx: Context) -> complex:
        idx = ctx.idx_query_fn(self)
        i, j = idx
        if i is None:
            vi = 0
        else:
            vi = ctx.x[i]
        if j is None:
            vj = 0
        else:
            vj = ctx.x[j]
        return (vi - vj) / self.resistance

