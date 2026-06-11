import math
from typing import Optional
import numpy as np

from ..base import Analysis
from .component import Component, Context, Stamper


class Diode(Component, Stamper):
    ''' connect as [anode,cathode] '''

    # Note on the diode limiter:
    # The diode limiter is a technique used to improve
    # the convergence of the nonlinear solver when simulating
    # circuits with diodes. The limiter works by limiting
    # the voltage across the diode to a certain value (the
    # critical voltage) during the nonlinear solve. This
    # prevents the diode current from becoming too large,
    # which can cause numerical issues and prevent convergence.
    # The limiter is only used during the nonlinear DC solve
    # to obtain the operating point and transient analysis,
    # and it is not used during AC nalysis.
    #
    # The DIODE_LIMITER_NVT constant controls the aggressiveness
    # of the limiter. A smaller value will result in more aggressive
    # limiting, while a larger value will result in less aggressive
    # limiting. The choice of this constant can affect the convergence
    # of the solver and the accuracy of the simulation, so it may
    # need to be adjusted based on the specific circuit being simulated.
    # Examples: see issues/diode_voltage_test.py and examples/ideal_diode_with_opamp.py
    #
    # The unit of DIODE_LIMITER_NVT is n*Vt (volts), and it represents
    # the voltage at which the limiter starts to take effect.
    # For example, if DIODE_LIMITER_NVT is set to 1, then the
    # limiter will start to take effect when the voltage across
    # the diode exceeds 1*n*Vt (which is typically around 0.025 volts
    # for a silicon diode at room temperature). If DIODE_LIMITER_NVT
    # is set to 10, then the limiter will start to take effect when
    # the voltage across the diode exceeds 10*n*Vt (which is typically
    # around 0.25 volts for a silicon diode at room temperature).
    #
    # The constant DIODE_LIMITER_NVT is only used for the more
    # sophisticated logarithmic limiter, and it is not used for
    # the simple clipping limiter. The simple clipping limiter
    # simply clips the voltage across the diode to a fixed value
    # (e.g. 0.8 volts), regardless of the value of DIODE_LIMITER_NVT.
    DIODE_LIMITER_NVT = 5

    # The DIODE_VOLTAGE_CLIP constant is used for the simple
    # clipping limiter. It represents the maximum voltage that
    # the diode can have across it during the nonlinear solve.
    # If the voltage across the diode exceeds this value, it
    # will be clipped to this value. This can help improve
    # convergence in some cases, but it also means that the
    # diode will not be accurately modeled above this voltage.
    # The choice of this constant can affect the accuracy of
    # the simulation, so it may need to be adjusted based on
    # the specific circuit being simulated.
    DIODE_VOLTAGE_CLIP = 0.8

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
        self.v_old = None

        # Note that the simple limiter as implemented
        # makes the diode linear above DIODE_VOLTAGE_CLIP volts. This
        # makes some simulations above DIODE_VOLTAGE_CLIP volts easier
        # to converge, but it also means that the diode is not accurately
        # modeled above DIODE_VOLTAGE_CLIP volts. The more
        # sophisticated limiter allows the diode to be accurately modeled
        # up to much higher voltages, but it may make some simulations
        # harder to converge.
        self._simple_limiter = True # set to False to use the more sophisticated limiter instead of simple clipping


    # TODO only required because the MNA solver expects
    # this method to exist for all components. We should
    # refactor the solver to not require this for
    # non-linear components.
    def admittance(self):
        # Should never be called
        assert False, "Diode is a non-linear component and does not have a fixed admittance. Use the stamp method to account for its non-linearity."

    def __component_typename__(self) -> str:
        return "D"

    def __value__(self) -> str | None:
        return None

    def linear(self):
        return False

    def stamp(self, ctx: Context):
        match ctx.analysis_type:
            case Analysis.AC:
                self._stamp_for_ac(ctx)
            case Analysis.DC:
                self._stamp_for_dc(ctx)
            case Analysis.TRANSIENT:
                self._stamp_for_dc(ctx)
            case Analysis.IC:
                self._stamp_for_dc(ctx)


    def _stamp_for_ac(self, ctx: Context):
        g = self.admittance_ac
        i, j = ctx.idx_query_fn(self)
        if i is not None:
            ctx.Y[i, i] += g
        if j is not None:
            ctx.Y[j, j] += g
        if i is not None and j is not None:
            ctx.Y[i, j] -= g
            ctx.Y[j, i] -= g

    def _limit_voltage(self, vd: complex) -> complex:
        if self.v_old is None:
            return vd

        if self._simple_limiter:
            # simple clipping to the critical voltage, which is the voltage
            # at which the diode current reaches a certain threshold (e.g. 1A)
            mag = abs(vd)
            if mag == 0:
                return 0j
            else:
                ph = vd / mag
                if mag > self.DIODE_VOLTAGE_CLIP:
                    mag = self.DIODE_VOLTAGE_CLIP
                return mag * ph
        else:
            vr = vd.real
            vi = vd.imag

            vold = self.v_old.real
            dv = vr - vold
            vt = self.nvt

            # soft logarithmic limiting
            # The constant (in this case 100) can be adjusted
            # to control how aggressive the limiting is.
            # A smaller constant will result in more
            # aggressive limiting, while a larger constant
            # will result in less aggressive limiting.
            # A more aggressive limiter may make life
            # harder for the nonlinear solver to converge,
            # but can help prevent numerical issues in some cases.
            nvt = self.DIODE_LIMITER_NVT * vt
            if dv > nvt:
                vr = vold + nvt * math.log1p(dv / nvt)

            elif dv < -nvt:
                vr = vold - nvt * math.log1p(-dv / nvt)

            return complex(vr, vi)


    def _stamp_for_dc(self, ctx: Context):
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

        vd = self._limit_voltage(vi-vj)
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
        if ctx.analysis_type == Analysis.AC:
            # The limiter is not relevant for AC simulations. The limiter is only
            # relevant during the nonlinear DC solve used to obtain the operating point.
            return self.admittance_ac * (vi - vj)
        else:
            vd = vi - vj
            vr = vd.real

            # Prevent reverse exponential blowup
            if vr < -40 * self.nvt:
                return -self.Is

            # Prevent forward overflow
            arg = min(vr / self.nvt, 40)

            i = self.Is * (math.exp(arg) - 1) # Shockley diode equation

            return complex(i, 0)
