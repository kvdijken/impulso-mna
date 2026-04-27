from typing import Dict, List, Tuple, Optional, Type, Any

from .component import Component, Context

LARGE_CONDUCTANCE = 1e12


class Wire(Component):
    """ Ideal wire with zero resistance and no voltage drop. """

    def __init__(self, id: Optional[str] = None):
        super().__init__(id)
        
    def admittance(self, s: Optional[complex] = None) -> complex:
        return LARGE_CONDUCTANCE
    
    def augments(self):
        return True
    
    def stamp(self, ctx: Context):
        idx = ctx.idx_query_fn(self)
        augm = ctx.augm_query_fn(self)
        i, j = idx
        if i is not None:
            ctx.Y[i, augm] -= 1
            ctx.Y[augm, i] -= 1
        if j is not None:
            ctx.Y[j, augm] += 1
            ctx.Y[augm, j] += 1
        ctx.z[augm] = 0 # volts
    
    def current(self, ctx: Context) -> complex:
        idx = ctx.augm_query_fn(self)
        return ctx.x[idx]


