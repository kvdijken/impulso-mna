from typing import Dict, List, Tuple, Optional, Type, Any

import numpy as np

from ..base import Analysis
from .source import PowerSource
from ..components.component import Context


class SinusoidalVoltageSource(PowerSource):
    '''
    '''
    def __init__(self,
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
        ac_analysis = ctx.analysis_type == Analysis.AC

        if ac_analysis:
            if self.ac_source:
                v = np.exp(1j * self.phase) # phasor representation of the sinusoidal voltage
            else:
                v = 0
        else:
            if self.ac_source:
                # In DC analysis, we treat the AC source as a short circuit, so the voltage is 0.
                v = 0
            else:
                v = self.voltage_at_time(ctx.t)

        idx = ctx.idx_query_fn(self)
        augm = ctx.augm_query_fn(self)
        i, j = idx
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


