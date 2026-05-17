import math
from typing import Optional
import numpy as np

from ..base import Analysis
from .component import Component, Context, Stamper


class Diode(Component, Stamper):
    ''' connect as [anode,cathode] '''

    def __init__(self,
                 Is: float = 2.52e-9,
                 n: float = 1.752,
                 vt: float = 0.02585,
                 id: Optional[str] = None):
        super().__init__(id)
        self.Is = Is
        self.n = n
        self.vt = vt
        self.nvt = n * vt
        self.v_crit = self.nvt * math.log(self.nvt / (math.sqrt(2) * self.Is))
        self.v_old = 0

    def reset(self):
        self.v_old = 0

    # TODO only required because the MNA solver expects
    # this method to exist for all components. We should
    # refactor the solver to not require this for
    # non-linear components.
    def admittance(self):
        # Should never be called
        assert False, "Diode is a non-linear component and does not have a fixed admittance. Use the stamp method to account for its non-linearity."

    def augments(self):
        return False

    def linear(self):
        return False

    def stamp(self, ctx: Context):
        if ctx.analysis_type == Analysis.AC:
            self.stamp_for_ac(ctx)
        else:
            self.stamp_for_dc(ctx)


    def stamp_for_ac(self, ctx: Context):
        g = self.admittance_ac
        i, j = ctx.idx_query_fn(self)
        if i is not None:
            ctx.Y[i, i] += g
        if j is not None:
            ctx.Y[j, j] += g
        if i is not None and j is not None:
            ctx.Y[i, j] -= g
            ctx.Y[j, i] -= g


    def stamp_for_dc(self, ctx: Context):
        # stamp using companion model
        i, j = ctx.idx_query_fn(self)
        if i is None:
            vi = 0
        else:
            vi = ctx.x[i]
        if j is None:
            vj = 0
        else:
            vj = ctx.x[j]
        vd = np.real(vi - vj)

            # limit the voltage to avoid numerical issues with the exponential
    #        if vd > self.v_crit:
    #            _L = 1 + (vd - self.v_old) / (self.n * self.vt)
    #            if _L < 0:
    #                pass
    #            else:
    #                vd = self.v_old + self.n * self.vt * math.log(_L)

        if True:   # simpler limiting strategy that just caps the voltage difference across the diode
            vd = min(vd, 0.8)   # crude but effective
        else:
            if vd > self.v_old:
                vd = min(vd, self.v_old + 0.1)
            else:
                vd = max(vd, self.v_old - 0.1)
        self.v_old = vd

        # Calculate the diode current and conductance (companion model)
        vdnvt = vd / self.nvt
        expvd = np.exp(vdnvt)
        i_eq = self.Is * (expvd * (1 - vdnvt) - 1)
        G = self.Is / self.nvt * expvd

        # Stamp the conductance (Y) and current source (z) contributions
        if i is not None:
            ctx.Y[i, i] += G
            ctx.z[i] -= i_eq
        if j is not None:
            ctx.Y[j, j] += G
            ctx.z[j] += i_eq
        if i is not None and j is not None:
            ctx.Y[i, j] -= G
            ctx.Y[j, i] -= G


    def set_admittance_for_ac(self,
                              i_dc: complex, # DC current through the diode at the operating point
                              ) -> None:
        # Start with diode equation
        # Eq 1: Differentiate wrt voltage to get small-signal conductance: g = di/dv = (Is / (n*vt)) * exp(vd / (n*vt))
        # From DC operating point analysis we know the diode current: i_dc = Is * (exp(vd / (n*vt)) - 1)
        # exp(vd / (n*vt)) >> 1, so i_dc ≈ Is * exp(vd / (n*vt))   ( this is a simplification)
        # i_dc = Is * exp(vd / (n*vt))
        # enter this in (1)
        self.admittance_ac = i_dc / (self.n * self.vt)


    def current(self, ctx: Context) -> complex:
        i, j = ctx.idx_query_fn(self)
        if i is None:
            vi = 0
        else:
            vi = ctx.x[i]
        if j is None:
            vj = 0
        else:
            vj = ctx.x[j]

        vd = vi - vj
        if ctx.analysis_type == Analysis.AC:
            return self.admittance_ac * vd
        else:
            vd = np.real(vd) # to prevent warning about complex values in the exponential, even though the imaginary part should be negligible
            return self.Is * (math.exp(vd/ (self.nvt)) - 1)

