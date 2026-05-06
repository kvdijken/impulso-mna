import numpy as np
from typing import Dict, List, Tuple, Optional, Type, Any

from .source import PowerSource
from ..components.component import Component, Context
from ..components.resistor import Resistor
from ..components.capacitor import Capacitor
from .dcvoltagesource import DCVoltageSource


class CCVS(PowerSource):
    # Current Controlled Voltage Source
    
    def __init__(self,
                 rm: float, # transresistance gain in Ohms (V/A)
                 id: Optional[str] = None):
        self.rm = rm
        super().__init__(id)

    def admittance(self, s: Optional[complex] = None) -> complex:
        return np.inf
    
    def connect(self, component: Component):
#        assert(isinstance(component, (Resistor,Capacitor,DCVoltageSource)))
        self.component = component

    def voltage(self,
                currents: Dict[Component, complex] # component -> current
                ) -> complex:
        # This assumes the current through a voltage source has been corrected already
        return self.rm * currents[self.component]

    def augments(self):
        return True
    
    def stamp(self, ctx: Context):
        i, j = ctx.idx_query_fn(self)
        augm = ctx.augm_query_fn(self)
        if i is not None:
            ctx.Y[i, augm] += 1 # current equation
            ctx.Y[augm, i] -= 1 # voltage equation
        if j is not None:
            ctx.Y[j, augm] -= 1 # current equation
            ctx.Y[augm, j] += 1 # voltage equation

        # Control current contribution
        comp = self.component # controlling component
        if isinstance(comp, (Resistor, Capacitor)):
            Ypq = comp.admittance(ctx.s)
            p, q = ctx.idx_query_fn(comp)
            if p is not None:
                ctx.Y[augm, p] += self.rm * Ypq
            if q is not None:
                ctx.Y[augm, q] -= self.rm * Ypq
        elif isinstance(comp,DCVoltageSource):
            augm_vs = ctx.augm_query_fn(comp)
            ctx.Y[augm, augm_vs] -= self.rm


    
    def current(self, ctx: Context) -> complex:
        idx = ctx.augm_query_fn(self)
        return ctx.x[idx]
    

