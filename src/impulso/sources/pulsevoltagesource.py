import numpy as np
from typing import Dict, List, Tuple, Optional, Type, Any

from .source import PowerSource
from ..components.component import Context
from ..base import  Analysis

class PulseVoltageSource(PowerSource):
    '''
    '''
    def __init__(self,
                 v1: float,
                 v2: float,
                 delay: float,
                 rise_time: float,
                 fall_time: float,
                 pulse_width: float,
                 period: float,
                 n_periods: Optional[int] = None,
                 id: Optional[str] = None):
        super().__init__(id=id)
        self.v1 = v1
        self.v2 = v2
        self.delay = delay
        self.rise_time = rise_time
        self.fall_time = fall_time
        self.pulse_width = pulse_width
        self.period = period
        self.n_periods = n_periods

    def admittance(self, s: Optional[complex] = None) -> complex:
        return np.inf  # ideal voltage source has infinite admittance (zero impedance)
    
    def voltage_at_time(self, t) -> float:
        # This is a simplified implementation and does
        # not handle all edge cases (e.g., rise/fall
        # time overlapping with the next pulse).
        # A full implementation would need to
        # account for these cases.
        # TODO: implement full behavior according to the specifications
        if t < self.delay:
            return self.v1
        # n_periods
        if self.n_periods is not None:
            if t >= (self.delay + self.n_periods * self.period):
                return self.v1
        
        time_in_period = (t - self.delay) % self.period
        if time_in_period < self.rise_time:
            return self.v1 + (self.v2 - self.v1) * (time_in_period / self.rise_time)
        elif time_in_period < self.rise_time + self.pulse_width:
            return self.v2
        elif time_in_period < self.rise_time + self.pulse_width + self.fall_time:
            return self.v2 - (self.v2 - self.v1) * ((time_in_period - self.rise_time - self.pulse_width) / self.fall_time)
        else:
            return self.v1
        
    def augments(self):
        return True
    
    def stamp(self, ctx: Context):
        assert ctx.analysis_type == Analysis.TRANSIENT, "PulseVoltageSource is only valid for transient analysis"
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
