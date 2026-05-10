from typing import Dict, List, Tuple, Optional, Type, Any

from .component import Component, Context
from ..base import Analysis


class Capacitor(Component):

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

    def augments(self):
        return False

    def stamp(self, ctx: Context):

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

            n1, n2 = ctx.nodes_query_fn(self)
            if n1 == ctx.ground_node:
                v1 = 0.0
            else:
                v1 = ctx.voltage_history[-1][n1]
            if n2 == ctx.ground_node:
                v2 = 0.0
            else:
                v2 = ctx.voltage_history[-1][n2]
            G = self.capacitance / ctx.dt
            i_eq = G * (v2 - v1)

            i, j = ctx.idx_query_fn(self)
            stamp_as_resistor(i,j,G)
            if i is not None:
                ctx.z[i] -= i_eq
            if j is not None:
                ctx.z[j] += i_eq

        if ctx.analysis_type == Analysis.TRANSIENT:
            stamp_transient()
        else:
            stamp_not_transient()

    def current(self, ctx: Context) -> complex:

        def current_transient():
            '''
            From pycircuit_new
            if integration_method == "backward_euler":
                # BE: I = C*(Vt - Vprev)/dt
                i_comp = c.capacitance * ((v1 - v2) - Vprev) / dt
            '''
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

            m, n = ctx.nodes_query_fn(self)
            if m == ctx.ground_node:
                vm = 0.0
            else:
                vm = ctx.voltage_history[-1][m]
            if n == ctx.ground_node:
                vn = 0.0
            else:
                vn = ctx.voltage_history[-1][n]
            v_prev = vn - vm
            return -self.capacitance * (v_curr - v_prev) / ctx.dt

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



