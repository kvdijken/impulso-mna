from typing import Dict, List, Tuple, Optional, Type, Any
import numpy as np

from .source import PowerSource
from ..components.component import Context


class VCVS(PowerSource):
    '''
    Voltage Controlled Voltage Source
    Connect as [out-, out+, in-, in+], where current flows from out- to out+ and
      control voltage is measured from in- to in+.
    '''

    # Node index mapping for clarity
    # The VCVS has 4 nodes: output negative,
    # output positive, input negative, input positive
    __out_neg = 0
    __out_pos = 1
    __in_neg = 2
    __in_pos = 3

    def __init__(self, *,
                 A: float,
                 id: Optional[str] = None):
        self.A = A
        super().__init__(id=id)

    def admittance(self, s: Optional[complex] = None) -> complex:
        return np.inf

    def augments(self):
        return True

    def stamp(self, ctx: Context):
        nodes = ctx.idx_query_fn(self)
        augm = ctx.augm_query_fn(self)
        i = nodes[VCVS.__out_neg]
        j = nodes[VCVS.__out_pos]
        p = nodes[VCVS.__in_neg]
        q = nodes[VCVS.__in_pos]

        if i is not None:
            ctx.Y[i, augm] -= -1
            ctx.Y[augm, i] -= 1
        if j is not None:
            ctx.Y[j, augm] += -1
            ctx.Y[augm, j] += 1

        # Control voltage contribution
        if p is not None:
            ctx.Y[augm, p] += self.A
        if q is not None:
            ctx.Y[augm, q] -= self.A


    def current(self, ctx: Context) -> complex:
        idx = ctx.augm_query_fn(self)
        return ctx.x[idx]



