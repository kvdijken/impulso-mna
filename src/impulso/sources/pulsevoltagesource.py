import numpy as np
from typing import Dict, List, Tuple, Optional, Type, Any

from .source import PowerSource
from ..components.component import Context
from ..base import  Analysis

class PulseVoltageSource(PowerSource):
    '''
    '''
    def __init__(self, *,
                 v1: float,          # low voltage level
                 v2: float,          # high voltage level
                 delay: float,       # signal train starts after delay
                 rise_time: float,   # time to rise from low to high level
                 fall_time: float,   # time to drop from high to low level
                 pulse_width: float, # time to stay on high level
                 period: float,      # rise-time + pulse-width + fall-time + time on low level
                 n_periods: Optional[int] = None, # number of pulses
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
            # Still in rise-time
            return self.v1 + (self.v2 - self.v1) * (time_in_period / self.rise_time)
        elif time_in_period < self.rise_time + self.pulse_width:
            # After rise, but before fall
            return self.v2
        elif time_in_period < self.rise_time + self.pulse_width + self.fall_time:
            # In fall-time
            return self.v2 - (self.v2 - self.v1) * ((time_in_period - self.rise_time - self.pulse_width) / self.fall_time)
        else:
            return self.v1

    def augments(self):
        return True

    def stamp(self, ctx: Context):
        assert ctx.analysis_type == Analysis.TRANSIENT, "PulseVoltageSource is only valid for transient analysis"
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
