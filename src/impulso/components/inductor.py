from __future__ import annotations
from typing import List, Optional, Type, TYPE_CHECKING
import numpy as np

from .component import Component, CircuitItem, Context
from ..base import Analysis
from ..helperregistry import registry, StampingHelper, Factory

if TYPE_CHECKING:
    from ..circuit import Circuit


LARGE_CONDUCTANCE = 1e12


class InductorGroup(StampingHelper):
    """
    A group of inductors that are mutually coupled.

    This is a helper class to manage the mutual
    coupling between multiple inductors.
    """
    _tol = 1e-6

    def __init__(self,
                 circuit: Circuit,
                 ctx: Context):
        self._circuit = circuit

        # Get the inductors and mutual inductances from the circuit
        self._inductors: dict[Inductor, int] = {} # map from Inductor to local _L index
        self._n = 0
        for comp in circuit.components:
            if isinstance(comp, Inductor):
                self._inductors[comp] = self._n
                self._n += 1
        self._mutuals: List[MutualInductance] = [c for c in circuit.components if isinstance(c, MutualInductance)]

        # node indices into MNA matrix for each inductor
        self._node_indices = {}
        for local_idx, ind in enumerate(self._inductors):
            self._node_indices[local_idx] = ctx.idx_query_fn(ind)

        self._n = len(self._inductors)

        # Create the mapping from local index in inductance matrix _L -> global index in admittance matrix
        self._local_to_global_idx: List[int] = []
        for i, ind in enumerate(self._inductors):
            self._local_to_global_idx.append(ctx.augm_query_fn(ind))

        # Calculate inductance matrix _L
        self._L = np.diag([ind.inductance for ind in self._inductors])
        for mutual in self._mutuals:
            M = mutual.mutual_M()
            L1 = mutual.L1
            L2 = mutual.L2
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

    def returns_current(self) -> bool:
        return False

    def _stamp_ac(self, ctx: Context):
        Z = ctx.s * self._L
        k = np.array(self._local_to_global_idx)
        ix_ = np.ix_(k, k)
        ctx.Y[ix_] -= Z

    def _stamp_transient(self, ctx: Context):
        Z = self._L / ctx.dt
        k = np.array(self._local_to_global_idx)
        ix_ = np.ix_(k, k)
        ctx.Y[ix_] -= Z

        i_prev = np.array([ctx.current_history[-1][ind] for ind in self._inductors])
        ctx.z[k] -= Z @ i_prev

    def stamp(self, ctx: Context):
        # Stamp topology
        for m in range(self._n):
            k = self._local_to_global_idx[m]
            i, j = self._node_indices[m]
            if i is not None:
                ctx.Y[i, k] += 1
                ctx.Y[k, i] += 1
            if j is not None:
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

    def augments(self):
        return True

    def current(self, ctx: Context) -> complex:
        idx = ctx.augm_query_fn(self)
        return ctx.x[idx]


class MutualInductance(CircuitItem):
    """
    Coupling between two inductors.

    M = k * sqrt(L1 * L2)
    """

    def __init__(self,
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


class InductorGroupFactory(Factory):
    def creates(self) -> Type[StampingHelper]:
        return StampingHelper

    def create_helper(self,
                      circuit: Circuit,
                      ctx: Context) -> StampingHelper:
        inductors = [c for c in circuit.components if isinstance(c, Inductor)]
        if len(inductors) == 0:
            return None
        # TODO: one InductorGroup per Circuit
        return InductorGroup(circuit, ctx)



registry.register_factory("InductorGroup", InductorGroupFactory())


