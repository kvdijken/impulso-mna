from typing import Optional
from unittest import case

import numpy as np

from ..base import Analysis
from .source import PowerSource
from ..components.component import Context


class SinusoidalVoltageSource(PowerSource):
    '''
    '''
    def __init__(self, *,
                 amplitude: float,  # amplitude is half Vpp, not used in AC simulation
                 frequency: float = None,
                 phase: float = 0.0,        # in radians
                 dc: float = 0.0,          # DC offset
                 ac_source: bool = False,     # whether this source should be included in AC analysis
                 id: Optional[str] = None):
        super().__init__(ac_source=ac_source, id=id)
        self.frequency = frequency
        self.amplitude = amplitude
        self.phase = phase
        self.dc = dc

    def admittance(self, s: Optional[complex] = None) -> complex:
        return np.inf

    def voltage_at_time(self, t) -> float:
        return self.dc + self.amplitude * np.sin(2 * np.pi * self.frequency * t + self.phase)

    def augments(self):
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


        if False:
            if ctx.analysis_type == Analysis.AC:
                if self.ac_source:
                    v = self.amplitude * np.exp(1j * self.phase) # phasor representation of the sinusoidal voltage
                else:
                    v = 0
            else:
                if self.ac_source:
                    # In DC analysis, we treat the AC source
                    # as a short circuit, so the voltage is
                    # the DC offset.
                    v = self.dc
                else:
                    v = self.voltage_at_time(ctx.t)

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


