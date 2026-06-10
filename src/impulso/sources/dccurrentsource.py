from typing import Optional

from quantiphy import Quantity

from ..base import Analysis
from .source import PowerSource
from ..components.component import Context, Stamper


class DCCurrentSource(PowerSource, Stamper):
    """
    Independent DC current source.

    Positive current flows from nodes[0] → nodes[1].
    """

    def __init__(
        self, *,
        current: float,
        id: Optional[str] = None,
    ):
        """
        Args:
            component_id: unique ID
            nodes: [n1, n2] (current flows n1 -> n2)
            current: current in Amperes
        """
        self._current = current
        super().__init__(id=id)

    def __component_typename__(self) -> str:
        return "DCCS"

    def __value__(self) -> str | None:
        return Quantity(self.current,"A").render(form="si",spacer="")

    def set_current(self, current: float):
        self._current = current

    def admittance(self, s: Optional[complex] = None) -> complex:
        return 0.0

    def stamp(self, ctx: Context):
        p, q = ctx.idx_query_fn(self)
        if ctx.analysis_type != Analysis.AC:
            # In AC analysis, we treat a DC current source as an open circuit, so we don't stamp anything.
            i = self._current
            if p is not None:
                ctx.z[p] -= i # amps
            if q is not None:
                ctx.z[q] += i # amps

    def current(self, ctx: Context) -> complex:
        return self._current


