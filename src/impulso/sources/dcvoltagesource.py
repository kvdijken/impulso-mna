from numba import jit
from typing import Dict, List, Tuple, Optional, Type, Any

from ..base import Analysis
from .source import VoltageSource
from ..components.component import Context


class DCVoltageSource(VoltageSource):
    """
    Voltage source component.
    """

    def admittance(self, s: Optional[complex] = None) -> complex:
        """Calculate admittance (1/impedance) for AC analysis."""
        pass
        
    def augments(self):
        return True
    
    def stamp(self, ctx: Context):
        i, j = ctx.idx_query_fn(self)
        augm = ctx.augm_query_fn(self)
        if i is not None:
            ctx.Y[i, augm] += 1
            ctx.Y[augm, i] -= 1
        if j is not None:
            ctx.Y[j, augm] -= 1
            ctx.Y[augm, j] += 1
            
        if ctx.analysis_type == Analysis.AC:
            ctx.z[augm] = 0 # volts
        else:
            ctx.z[augm] = self.voltage # volts
    
    def current(self, ctx: Context) -> complex:
        idx = ctx.augm_query_fn(self)
        return ctx.x[idx]
    
    

