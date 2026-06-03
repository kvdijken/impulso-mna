from typing import Optional

from .component import Component, Context, Stamper
from ..base import Analysis


class Capacitor(Component, Stamper):

    def __init__(self,
                 capacitance: float,
                 initial_voltage: float = 0.0, # initial voltage V[1]-V[0]
                 id: Optional[str] = None):
        if capacitance < 0:
            raise ValueError(f"Capacitance must be non-negative, got {capacitance}")
        super().__init__(id)
        self.capacitance = capacitance
        self.initial_voltage = initial_voltage

    def admittance(self, s: Optional[complex] = None) -> complex:
        return s * self.capacitance()

    def augments(self, ctx: Context) -> bool:
        return (ctx.analysis_type == Analysis.IC) and (self.initial_voltage != 0)

    def init_state(self):
        # For transient analysis, we can initialize the voltage across the capacitor at t=0
        self.previous_voltage = self.initial_voltage

    def update_state(self, ctx: Context):
        i, j = ctx.idx_query_fn(self)
        if i is None:
            v1 = 0
        else:
            v1 = ctx.x[i]
        if j is None:
            v2 = 0
        else:
            v2 = ctx.x[j]
        self.previous_voltage = v2 - v1

    def stamp(self, ctx: Context):

        def stamp_initial_condition():
            # For the initial condition, we can treat the
            # capacitor as a voltage source with the initial voltage
            i, j = ctx.idx_query_fn(self)
            augm = ctx.augm_query_fn(self)
            if i is not None:
                ctx.Y[i, augm] += 1
                ctx.Y[augm, i] -= 1
            if j is not None:
                ctx.Y[j, augm] -= 1
                ctx.Y[augm, j] += 1
            ctx.z[augm] = self.initial_voltage # volts

        def stamp_not_transient():
            y = ctx.s * self.capacitance
            i, j = ctx.idx_query_fn(self)
            if i is not None:
                ctx.Y[i, i] += y
            if j is not None:
                ctx.Y[j, j] += y
            if i is not None and j is not None:
                ctx.Y[i, j] -= y
                ctx.Y[j, i] -= y

        def stamp_transient():

            def stamp_as_resistor(i,j,g):
                if i is not None:
                    ctx.Y[i, i] += g
                if j is not None:
                    ctx.Y[j, j] += g
                if i is not None and j is not None:
                    ctx.Y[i, j] -= g
                    ctx.Y[j, i] -= g

            G = self.capacitance / ctx.dt
            i_eq = G * self.previous_voltage

            i, j = ctx.idx_query_fn(self)
            stamp_as_resistor(i,j,G)
            if i is not None:
                ctx.z[i] -= i_eq
            if j is not None:
                ctx.z[j] += i_eq

#        if ctx.analysis_type == Analysis.IC:
        if ctx.analysis_type == Analysis.IC and self.augments(ctx):
            stamp_initial_condition()
        elif ctx.analysis_type == Analysis.TRANSIENT:
            stamp_transient()
        else:
            stamp_not_transient()

    def current(self, ctx: Context) -> complex:

        def current_transient():
            i, j = ctx.idx_query_fn(self)
            if i is None:
                vi = 0
            else:
                vi = ctx.x[i]
            if j is None:
                vj = 0
            else:
                vj = ctx.x[j]
            v_curr = vj - vi
            return -self.capacitance * (v_curr - self.previous_voltage) / ctx.dt

        def current_not_transient():
            i, j = ctx.idx_query_fn(self)
            if i is None:
                vi = 0
            else:
                vi = ctx.x[i]
            if j is None:
                vj = 0
            else:
                vj = ctx.x[j]
            return ctx.s * self.capacitance * (vi - vj)

        if ctx.analysis_type == Analysis.TRANSIENT:
            return current_transient()
        else:
            return current_not_transient()



