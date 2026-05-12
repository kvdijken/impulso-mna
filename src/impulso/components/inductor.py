from typing import Dict, List, Tuple, Optional, Type, Any
import numpy as np

from .component import Component, CircuitItem, Context
from ..base import Analysis

LARGE_CONDUCTANCE = 1e12


class CoupledInductorGroup(CircuitItem):
    """
    A group of inductors that are mutually coupled.

    This is a helper class to manage the mutual
    coupling between multiple inductors.
    """

    def __init__(self):
        pass

    def stamp_L(self, ctx: Context, L: Inductor):
        # Stamping will be done by the mutual inductance, as it needs
        # to know about all inductors involved.
        pass

    def current_L(self, ctx: Context, L: Inductor) -> complex:
        # TODO: Implement the current calculation for a coupled inductor
        pass

    def augments_L(self, L: Inductor) -> bool:
        # Augments for the entire coupled inductor group
        return False

    def augments(self) -> bool:
        return True
    

class Inductor(Component):

    def __init__(
        self,
        inductance: float,
        dot_at_node1: bool = True,
        initial_current: float = 0.0,
        id: Optional[str] = None,
    ):
        if inductance < 0:
            raise ValueError(f"Inductance must be non-negative, got {inductance}")
        super().__init__(id)
        self.dot_at_node1 = dot_at_node1
        self.inductance = inductance
        self.initial_current = initial_current
        self.coupling = None  # type: Optional[CoupledInductorGroup]

    def admittance(self, s: Optional[complex] = None) -> complex:
        return 1 / (s * self.inductance())

    def dc_conductance(self):
        return LARGE_CONDUCTANCE  # treat inductor as short circuit in DC analysis

    def augments(self):
        if self.coupling is None:
            return True
        else:
            # Let the mutual inductance handle the augmentation,
            # as it needs to know about both inductors.
            return self.coupling.augments_L(L=self)

    def couple(self, M: MutualInductance):
        self.coupling = M

    def stamp(self, ctx: Context):

        def stamp_not_transient():
            i1, i2 = ctx.idx_query_fn(self)
            augm = ctx.augm_query_fn(self)
            if i1 is not None:
                ctx.Y[i1, augm] += 1
                ctx.Y[augm, i1] += 1
            if i2 is not None:
                ctx.Y[i2, augm] -= 1
                ctx.Y[augm, i2] -= 1
            ctx.Y[augm, augm] -= ctx.s * self.inductance # ohm

        def stamp_transient():
            i1, i2 = ctx.idx_query_fn(self)
            augm = ctx.augm_query_fn(self)
            if i1 is not None:
                ctx.Y[i1, augm] += 1
                ctx.Y[augm, i1] += 1
            if i2 is not None:
                ctx.Y[i2, augm] -= 1
                ctx.Y[augm, i2] -= 1
            alpha = self.inductance / ctx.dt # ohm
            ctx.Y[augm,augm] -= alpha
            i_hist = ctx.current_history[-1][self]
            ctx.z[augm] += -alpha * i_hist

        if self.coupling is None:
            if ctx.analysis_type == Analysis.TRANSIENT:
                stamp_transient()
            else:
                stamp_not_transient()
        else:
            # Let the mutual inductance handle the stamping,
            # as it needs to know about both inductors.
            self.coupling.stamp_L(ctx=ctx, L=self)


    def current(self, ctx: Context) -> complex:
        if self.coupling is None:
            idx = ctx.augm_query_fn(self)
            return ctx.x[idx]
        else:
            # Let the mutual inductance handle the current
            # calculation, as it needs to know about both
            # inductors.
            return self.coupling.current_L(ctx=ctx, L=self)


class MutualInductance(CircuitItem):
    """
    Coupling between two inductors.

    M = k * sqrt(L1 * L2)
    """

    def __init__(self, *,
                 L1: Inductor,
                 L2: Inductor,
                 coupling: float,
                 id: Optional[str] = None):

        if not (0 <= coupling <= 1):
            raise ValueError(f"Coupling coefficient must be between 0 and 1, got {coupling}")
        super().__init__(id)
        self.L1 = L1
        self.L2 = L2
        self.k = coupling
        if ((self.k < 0) or (self.k > 1)):
            raise ValueError(f"Coupling factor must be [0..1], got {self.k}")

    def mutual_M(self):
        M = self.k * np.sqrt(self.L1.inductance * self.L2.inductance)
        sign = 1.0
        if self.L1.dot_at_node1 != self.L2.dot_at_node1:
            sign = -1.0
        return sign * M

    def augments(self):
        return False

    def is_directive(self):
        return True

    def linear(self) -> bool:
        return True

    def stamp(self, ctx: Context):
        idx1 = ctx.augm_query_fn(self.L1)
        idx2 = ctx.augm_query_fn(self.L2)
        M = self.mutual_M()
        val = -ctx.s * M
        ctx.Y[idx1, idx2] += val
        ctx.Y[idx2, idx1] += val

