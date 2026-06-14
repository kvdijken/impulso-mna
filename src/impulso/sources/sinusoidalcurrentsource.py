from typing import Optional

from quantiphy import Quantity

import numpy as np

from ..base import Analysis
from .source import PowerSource
from ..components.component import Context

# TODO Create test for SINCS
class SinusoidalCurrentSource(PowerSource):
    """
    Independent Sinusoidal current source.

    Positive current flows from nodes[0] → nodes[1].
    """

    def __init__(
        self, *,
        amplitude: float,
        frequency: float,
        phase: float = 0, # in radians
        dc: float = 0.0,          # DC offset
        ac_source: bool = False,     # whether this source should be included in AC analysis
        id: Optional[str] = None,
    ):
        """
        Args:
            component_id: unique ID
            nodes: [n1, n2] (current flows n1 -> n2)
            current: current in Amperes
        """
        super().__init__(ac_source=ac_source, id=id)
        if frequency is None:
            assert self.is_ac()
            self.frequency = 0
        else:
            assert not self.is_ac()
            self.frequency = frequency
        self.amplitude = amplitude
        self.phase = phase
        self.dc = dc

    def __component_typename__(self) -> str:
        return "SINCS"

    def __value__(self) -> str | None:
        if self.ac_source:
            return "{A=" + Quantity(self.amplitude,"A").render(form="si",spacer="") + ", phi=" + str(self.phase) + " rad, DC=" + Quantity(self.dc,"A").render(form="si",spacer="") + ", AC}"
        else:
            return "{A=" + Quantity(self.amplitude,"A").render(form="si",spacer="") + ", phi=" + str(self.phase) + " rad, DC=" + Quantity(self.dc,"A").render(form="si",spacer="") + ", f=" + Quantity(self.frequency,"Hz").render(form="si",spacer="") + "}"

    def current_at_time(self, t) -> float:
        assert not self.is_ac()
        return self.dc + self.amplitude * np.sin(2 * np.pi * self.frequency * t + self.phase)

    def augments(self, ctx):
        return False

    def stamp(self, ctx: Context):
        ac_analysis = ctx.analysis_type == Analysis.AC

        if ac_analysis:
            if self.ac_source:
                # In AC analysis, we treat the sinusoidal current source as a phasor with magnitude equal to the amplitude and phase equal to the specified phase.
                i = self.amplitude * np.exp(1j * self.phase)
            else:
                # In AC analysis, we treat a DC current source as an open circuit, so we don't stamp anything.
                i = 0
        else:
            if self.ac_source:
                # In DC analysis, we treat the AC source
                # as a short circuit, so the current is
                # the DC offset.
                i = self.dc
            else:
                i = self.current_at_time(ctx.t)

        p, q = ctx.idx_query_fn(self)
        i = self.amplitude
        if p is not None:
            ctx.z[p] -= i # amps
        if q is not None:
            ctx.z[q] += i # amps

    def current(self, ctx: Context) -> complex:
        return self.amplitude


