import numpy as np
from typing import Dict, Optional

from .source import PowerSource
from ..components.component import Component, Context, Stamper
from ..components.resistor import Resistor
from ..components.capacitor import Capacitor
from .dcvoltagesource import DCVoltageSource


class CCVS(PowerSource, Stamper):
    # Current Controlled Voltage Source

    def __init__(self,
                 *,
                 rm: float, # transresistance gain in Ohms (V/A)
                 id: Optional[str] = None):
        self.rm = rm
        super().__init__(id=id)

    def admittance(self, s: Optional[complex] = None) -> complex:
        return np.inf

    def connect(self, component: Component):
        # Test the component is valid for connection
        if not isinstance(component, (Resistor,Capacitor,DCVoltageSource)):
            raise TypeError(f"CCVS can only be connected to a Resistor, Capacitor, or DCVoltageSource, got {type(component)}")
        # Note that it is still possible to connect to a component that is not
        # in the circuit, but this will be caught during stamping, with a more
        # ugly error message. We could also choose to catch this here, but it
        # would require passing the circuit object to the CCVS, which seems less clean.
        # Or upon adding a component to the circuit, we could notify
        # the component that it has been added to the circuit, and then the CCVS can check if the
        # component it is connected to has been added to the circuit. But this seems
        # like a lot of extra complexity for a check that will be caught during stamping anyway.
        self.component = component

    def voltage(self,
                currents: Dict[Component, complex] # component -> current
                ) -> complex:
        # This assumes the current through a voltage source has been corrected already
        return self.rm * currents[self.component]

    def augments(self, ctx: Context):
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


