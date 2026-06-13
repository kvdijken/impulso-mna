from typing import Dict, List, Tuple, Optional, Type, Any
import numpy as np

from .source import PowerSource
from ..components.component import Component, Context, Stamper, HasAdmittance
from .dcvoltagesource import DCVoltageSource
from ..components.resistor import Resistor
from ..components.capacitor import Capacitor


class CCCS(PowerSource, Stamper):
    # Current Controlled Current Source

    def __init__(self, *,
                 A: float,
                 id: Optional[str] = None):
        self.A = A
        super().__init__(id=id)

    def __value__(self) -> str | None:
        return str(self.A) + "*I(" + self.component.id + ")"

    def connect(self, component: HasAdmittance):
        assert(isinstance(component, (Resistor, Capacitor, DCVoltageSource)))
        self.component = component

    def stamp(self, ctx: Context):
        i, j = ctx.idx_query_fn(self) # indices for this CCCS
        control = self.component # controlling component
        if isinstance(control, DCVoltageSource):
            augm_vs = ctx.augm_query_fn(control)
            if i is not None:
                ctx.Y[i,augm_vs] += self.A
            if j is not None:
                ctx.Y[j,augm_vs] -= self.A
        else:
            # It has already been ascertained that the controlling
            # component is a DCVoltageSource, Resistor or
            # Capacitor. At this point we can assume it is either
            # Resistor or Capacitor, no more cheks needed.
            p, q = ctx.idx_query_fn(control)
            Ypq = control.admittance()
            # CCCS is connected from i to j
            # current flows THROUGH the CCCS from i to j
            if p is not None:
                if i is not None:
                    ctx.Y[i,p] += self.A * Ypq
                if j is not None:
                    ctx.Y[j,p] -= self.A * Ypq
            if q is not None:
                if i is not None:
                    ctx.Y[i,q] -= self.A * Ypq
                if j is not None:
                    ctx.Y[j,q] += self.A * Ypq

    def current(self, ctx: Context) -> complex:
        return self.A * self.component.current(ctx)

