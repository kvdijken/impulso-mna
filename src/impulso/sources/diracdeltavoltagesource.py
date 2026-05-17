import numpy as np
from typing import Optional

from .source import PowerSource
from ..components.component import Context, Stamper
from ..base import  Analysis

class DiracDeltaVoltageSource(PowerSource, Stamper):
    '''
    '''

    def __init__(self, *,
                 dt: float,
                 delay: float,
                 voltage: float = 1.0,
                 id: Optional[str] = None):
        super().__init__(id=id)
        self.dt = dt
        self.delay = delay
        self.voltage = voltage
        self.before = True

    def admittance(self, s: Optional[complex] = None) -> complex:
        return np.inf  # ideal voltage source has infinite admittance (zero impedance)

    def voltage_at_time(self, t) -> float:
        if self.before and t >= self.delay:
            self.before = False
            return self.voltage / self.dt
        else:
            return 0.0

    def reset(self):
        self.before = True

    def augments(self):
        return True

    def stamp(self, ctx: Context):
        assert ctx.analysis_type == Analysis.TRANSIENT, "DiracVoltageSource is only valid for transient analysis"
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
