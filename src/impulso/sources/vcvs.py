from typing import Optional, Tuple, List
import numpy as np

from .source import PowerSource
from ..components.component import Context
from ..base import Node


class VCVS(PowerSource):
    '''
    Voltage Controlled Voltage Source
    Connect as [out-, out+, in-, in+], where current flows from out- to out+ and
      control voltage is measured from in- to in+.
    '''
    vnodes: Tuple[Node, Node] # nodes controlling the voltage

    def __init__(self, *,
                 A: float,
                 id: Optional[str] = None):
        self.A = A
        super().__init__(id=id)

    def __component_typename__(self) -> str:
        return "VCVS"

    def connect(self, vnodes: Tuple[Node,Node]):
        self.vnodes = vnodes

    # TODO: create test
    def __value__(self) -> str | None:
        return str(self.A) + "*(V(" + str(self.vnodes[1]) + ")-V(" + str(self.vnodes[0]) + "))"

    def augments(self, ctx: Context):
        return True

    def stamp(self, ctx: Context):
        i, j = ctx.idx_query_fn(self)
        p, q = ctx.idx_query_fn(self.vnodes)
        augm = ctx.augm_query_fn(self)
#        i = nodes[VCVS.__out_neg]
#        j = nodes[VCVS.__out_pos]
#        p = nodes[VCVS.__in_neg]
#        q = nodes[VCVS.__in_pos]

        if i is not None:
            ctx.Y[i, augm] += +1
            ctx.Y[augm, i] += -1
        if j is not None:
            ctx.Y[j, augm] += -1
            ctx.Y[augm, j] += +1

        # Control voltage contribution
        if p is not None:
            ctx.Y[augm, p] += self.A
        if q is not None:
            ctx.Y[augm, q] -= self.A


    def current(self, ctx: Context) -> complex:
        augm = ctx.augm_query_fn(self)
        return ctx.x[augm]



