from typing import Optional
from unittest import case

import numpy as np
from quantiphy import Quantity

from ..base import Analysis
from .source import PowerSource
from ..components.component import Context


class SinusoidalVoltageSource(PowerSource):
    '''
    '''
    def __init__(self, *,
                 amplitude: float,  # amplitude is half Vpp, not used in AC simulation
                 frequency: Optional[float] = None,
                 phase: float = 0.0,        # in radians
                 dc: float = 0.0,          # DC offset
                 ac_source: bool = False,     # whether this source should be included in AC analysis
                 id: Optional[str] = None):
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
        return "SINVS"

    def __value__(self) -> str | None:
        if self.ac_source:
            return "{A=" + Quantity(self.amplitude,"V").render(form="si",spacer="") + ", phi=" + str(self.phase) + " rad, DC=" + Quantity(self.dc,"V").render(form="si",spacer="") + ", AC}"
        else:
            return "{A=" + Quantity(self.amplitude,"V").render(form="si",spacer="") + ", phi=" + str(self.phase) + " rad, DC=" + Quantity(self.dc,"V").render(form="si",spacer="") + ", f=" + Quantity(self.frequency,"Hz").render(form="si",spacer="") + "}"

    def voltage_at_time(self, t) -> float:
        return self.dc + self.amplitude * np.sin(2 * np.pi * self.frequency * t + self.phase)

    def augments(self, ctx: Context):
        return True

    def stamp(self, ctx: Context):
        match ctx.analysis_type:
            case Analysis.AC:
                if self.ac_source:
                    v = self.amplitude * np.exp(1j * self.phase) # phasor representation of the sinusoidal voltage
                else:
                    v = 0
            case Analysis.DC:
                if self.ac_source:
                    # In DC analysis, we treat the AC source
                    # as a short circuit, so the voltage is
                    # the DC offset.
                    v = self.dc
                else:
                    v = self.dc
            case Analysis.TRANSIENT:
                v = self.voltage_at_time(ctx.t)
            case Analysis.IC:
                v = self.voltage_at_time(0)

        i, j = ctx.idx_query_fn(self)
        augm = ctx.augm_query_fn(self)
        if i is not None:
            ctx.Y[i, augm] += 1
            ctx.Y[augm, i] -= 1
        if j is not None:
            ctx.Y[j, augm] -= 1
            ctx.Y[augm, j] += 1
        ctx.z[augm] = v # volts

    def current(self, ctx: Context) -> complex:
        idx = ctx.augm_query_fn(self)
        return ctx.x[idx]


