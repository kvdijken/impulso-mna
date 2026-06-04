"""
Capacitor component module.

This module defines the Capacitor component used by the circuit solver.
The capacitor supports standard frequency-domain admittance stamping,
transient companion-model stamping, and optional initial-condition
handling for initial condition (IC) analysis.

Key behavior:
- stores capacitance and optional initial voltage
- stamps frequency-domain capacitor admittance for non-transient analyses
- stamps a companion-model conductance plus history source in transient
  analysis
- stamps an auxiliary voltage source equation when an initial voltage is
  specified for IC analysis
- computes capacitor current consistently for transient and other analyses

What it does:
- Implements a capacitor element with a specified capacitance.
- Supports an optional initial_voltage for IC and transient initialization.
- Integrates with the solver by stamping its contribution into the
  system matrices and source vectors.
- Computes current through the capacitor for different analysis modes.

How it works:
- __init__: validates capacitance and stores initial_voltage.
- admittance(s): returns the capacitor's frequency-domain admittance s*C.
- augments(ctx): signals auxiliary equation use for IC initial voltage.
- init_state(): initializes previous voltage for transient analysis.
- update_state(ctx): records capacitor voltage after each solve step.
- stamp(ctx): stamps the matrix for IC, transient, or other analyses.
- current(ctx): computes current using transient or frequency-domain form.

Summary:
This module models a capacitor consistently across steady-state,
initial-condition, and transient analysis, while handling optional
initial voltage conditions and providing matrix stamping plus current
evaluation.
"""

from typing import Optional

from .component import Component, Context, Stamper
from ..base import Analysis


class Capacitor(Component, Stamper):

    def __init__(self,
                 capacitance: float,
                 initial_voltage: float | None = None, # initial voltage V[1]-V[0]
                                                       #
                                                       # if None, don't care; let the IC solve
                                                       # determine the capacitor voltage. This
                                                       # capacitor will be treated as a regular
                                                       # capacitor with no initial condition
                                                       # for the IC analysis, and will be
                                                       # initialized to the voltage as obtained
                                                       # from IC analysis at t=0 for transient
                                                       # analysis.
                                                       #
                                                       # if not None, this will be the initial
                                                       # voltage across the capacitor for the
                                                       # initial condition analysis (IC). For
                                                       # transient analysis, the capacitor will
                                                       # be initialized to this voltage at t=0.
                                                       #
                                                       # For parasitic capacitors, it's common
                                                       # to leave initial_voltage None, as setting
                                                       # it to a specific value could introduce
                                                       # convergence issues.
                 id: Optional[str] = None):
        if capacitance < 0:
            raise ValueError(f"Capacitance must be non-negative, got {capacitance}")
        super().__init__(id)
        self.capacitance = capacitance
        self.initial_voltage = initial_voltage

    def admittance(self, s: Optional[complex] = None) -> complex:
        return s * self.capacitance()

    def _has_initial_condition(self) -> bool:
        return self.initial_voltage is not None

    def augments(self, ctx: Context) -> bool:
        return (ctx.analysis_type == Analysis.IC) and self._has_initial_condition()

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

        def stamp_ac_dc():
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

        if (ctx.analysis_type == Analysis.IC) and self._has_initial_condition():
            stamp_initial_condition()
        elif ctx.analysis_type == Analysis.TRANSIENT:
            stamp_transient()
        else:
            # DC or AC
            stamp_ac_dc()

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



