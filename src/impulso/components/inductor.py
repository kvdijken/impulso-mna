from typing import Dict, List, Tuple, Optional, Type, Any
import numpy as np

from .component import Component, CircuitItem, Context
from ..base import Analysis

LARGE_CONDUCTANCE = 1e12


class InductorGroup(Component):
    """
    A group of inductors that are mutually coupled.

    This is a helper class to manage the mutual
    coupling between multiple inductors.
    """
    _tol = 1e-6

    def __init__(self, circuit: Circuit, ctx: Context):
        super().__init__(id=f"INDUCTOR_GROUP")
        self._circuit = circuit
        self._circuit.add(self, []) # to let itself be called for stamping

        # Get the inductors and mutual inductances from the circuit
        self._inductors: dict[Inductor, int] = {} # map from Inductor to local _L index
        self._n = 0
        for comp in circuit.component.values():
            if isinstance(comp, Inductor):
                self._inductors[comp] = self._n
                self._n += 1
        self._mutuals: List[MutualInductance] = [c for c in circuit.component.values() if isinstance(c, MutualInductance)]

        # node numbers
        self._nodes = {}
        for local_idx, ind in enumerate(self._inductors):
            self._nodes[local_idx] = circuit.nodes[ind]

        self._n = len(self._inductors)

        # Create the mapping from local index in inductance matrix _L -> global index in admittance matrix
        self._local_to_global_idx: Dict[int, int] = {}
        for i, ind in enumerate(self._inductors):
            self._local_to_global_idx[i] = ctx.augm_query_fn(ind)

        # Calculate inductance matrix _L
        self._L = np.diag([ind.inductance for ind in self._inductors])
        for mutual in self._mutuals:
            M = mutual.mutual_M()
            L1 = mutual.L1
            L2 = mutual.L2
            if L1.dot_at_node1 != L2.dot_at_node1:
                M = -M
            i = self._inductors[L1] # map into local _L index
            j = self._inductors[L2] # map into local _L index

            if (self._L[i,j] != 0) or (self._L[j,i] != 0):
                raise ValueError("Multiple mutual inductances between the same pair of inductors is not supported")
            self._L[i,j] = M
            self._L[j,i] = M

        # Validation
        self._validate_L()


    def _validate_L(self):
        # Symmetry
        assert(np.allclose(self._L, self._L.T)) # L must be symmetric
        # Positive semidefinite
        eigvals = np.linalg.eigvalsh(self._L)
        if np.any(eigvals < -self._tol):
            raise ValueError("Non-physical inductance matrix")


    def admittance(self, s: Optional[complex] = None) -> complex:
        """Calculate admittance (1/impedance) for AC analysis."""
        raise NotImplementedError("InductorGroup does not have a fixed admittance, it's just a helper for managing inductors")

    def augments(self) -> None:
        return False

    def returns_current(self) -> bool:
        return False

    def linear(self) -> bool:
        return True

    def _stamp_ac(self, ctx: Context):
        Z = ctx.s * self._L
        k = np.array(list(self._local_to_global_idx.values()))
        ctx.Y[np.ix_(k, k)] -= Z

    def _stamp_transient(self, ctx: Context):
        pass

    def stamp(self, ctx: Context):
        # Stamp topology
        for m in range(self._n):
            k = self._local_to_global_idx[m]
            i = self._nodes[m][0]
            j = self._nodes[m][1]
            if i != 0:
                ctx.Y[i, k] += 1
                ctx.Y[k, i] += 1
            if j != 0:
                ctx.Y[j, k] -= 1
                ctx.Y[k, j] -= 1

        # Stamp constitutive
        if ctx.analysis_type == Analysis.DC:
            pass
        elif ctx.analysis_type == Analysis.AC:
            self._stamp_ac(ctx)
        elif ctx.analysis_type == Analysis.TRANSIENT:
            self._stamp_transient(ctx)

    def current(self, ctx: Context) -> complex:
        raise NotImplementedError("InductorGroup does not have a current, it's just a helper for managing inductors")

    def before_add(self,
                   circuit: Circuit,
                   nodes: List[int]
                   ) -> Tuple[bool, bool]:
        # This component is not actually added to the circuit, it's just a
        # helper for managing inductors
        # Do return True for do_add, because it will need to do the stamping.
        # It does not return current, that will be left to the individual inductors.
        return True, False




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

    def stamps(self) -> bool:
        return False

    def admittance(self, s: Optional[complex] = None) -> complex:
        return 1 / (s * self.inductance())

    def dc_conductance(self):
        return LARGE_CONDUCTANCE  # treat inductor as short circuit in DC analysis

    def augments(self):
        return True

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

        if ctx.analysis_type == Analysis.TRANSIENT:
            stamp_transient()
        else:
            stamp_not_transient()


    def current(self, ctx: Context) -> complex:
        idx = ctx.augm_query_fn(self)
        return ctx.x[idx]


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
        if L1 == L2:
            raise ValueError("Mutual inductance cannot be defined between the same inductor")
        super().__init__(id)
        self.L1 = L1
        self.L2 = L2
        self.k = coupling

    def stamps(self) -> bool:
        return False

    def returns_current(self) -> bool:
        return False

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

