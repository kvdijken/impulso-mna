import os

from typing import Dict, List, Tuple, Type
import numpy as np
from collections import defaultdict
from functools import cache

from .base import Analysis, TopologyError
from .components.component import Component, Context
#from .components.inductor import Inductor, MutualInductance, InductorGroup
from .circuit import Circuit
from .sources.source import PowerSource
from .helperregistry import registry, StampingHelper, Factory


class Solver_ACDC():

    nodes: Dict[Component, List[int]]  # component -> connected nodes
    component: list[Component]  # component_id -> Component instance
    node_index: Dict[int, int] = {} # node number -> index in MNA matrix
    ground_node: int = 0
    augm_idx: Dict[Component, int] = {} # component -> index in MNA matrix for
                                        # augmented variables (currents through
                                        # voltage sources, etc.)

    def __init__(self,
                 circuit: Circuit,
                 ):
        self.circuit = circuit
        self._prepared = False
        self.nodes = circuit.nodes
        self.component = circuit.components
        self.ground_node = circuit.ground_node
        self.x_prev = None # previous solution vector, used for nonlinear iteration
        self.ctx = self.create_context()

        self._stamping_components = [] # components that need to be stamped in the MNA matrix (e.g. voltage sources, inductors, opamps, etc.)
        self._current_components = [] # components for which we want to extract currents after solving (e.g. voltage sources, inductors, opamps, etc.)



    def create_context(self) -> Context:
        ctx = Context()
        ctx.analysis_type = None
        ctx.s = None
        ctx.ground_node = self.ground_node
        ctx.idx_query_fn = self.get_node_indices
        ctx.augm_query_fn = self.get_augm_index
        ctx.nodes_query_fn = self.get_nodes
        return ctx


    @cache
    def get_nodes(self, comp):
        return self.nodes.get(comp, None)


    @cache
    def get_augm_index(self, comp):
        return self.augm_idx.get(comp, None)


    @cache
    def get_node_indices(self,
                     comp: Component
    ) -> List[int]:
        '''
        Return the indices of the nodes connected to the given component in the MNA matrix.
        If a node is the ground node, return None for its index since it does not have a corresponding row/column in the MNA matrix.
        '''
        return [self.node_index.get(n, None) for n in self.get_nodes(comp)]


    def solve(self,
              freq: float
              ) -> Tuple[Dict[int | str, complex], # node voltages
                         Dict[str | Component, complex]]: # currents through components
        """
        Solve the circuit for the given frequency and ground node.

        Returns:
            voltages: dict node -> complex voltage
            currents: dict comp_id | component -> complex current
        """
        self.node_administration()
        return self.solve_mna(freq)


    def all_components(self) -> List[Component]:
        """Return a list of all components in the circuit."""
        return self.component


    def node_administration(self):
        self.N, self.node_index = self.assign_node_indices()
        self.N = self.assign_augmented_slots(self.N)


    def all_nodes(self) -> List[int]:
        """Return a list of all nodes in the circuit."""
        return self.node_index.keys()


    def prepare_for_solving(self) -> None:
        # Prepare the circuit for solving

        # Get all the stamping helpers
        for name, provider in registry.factories(cls=StampingHelper):
            stamping_helper = provider.create_helper(self.circuit, self.ctx)
            if stamping_helper is not None:
                self._stamping_components.append(stamping_helper)
                stamping_helper.prepare(self.circuit, self.ctx)


    def solve_mna(self,
                  freq: float = 0,
                  return_real: bool = False
                  ) -> Tuple[Dict[int, complex],
                             Dict[str | Component, complex]]:
        """
        AC & DC small-signal MNA solver.

        Returns:
            voltages: dict node -> complex voltage
            currents: dict comp_id | component -> complex current
        """
        converged = False

        self.ctx.s = 1j * 2 * np.pi * freq
        if self.ctx.analysis_type is None:
            self.ctx.analysis_type = Analysis.AC if freq != 0 else Analysis.DC

        # Prepare the circuit for solving.
        # Do this at the very last moment just before solving, when everything  is ready,
        # since some components may need to know the node indices for preparation.
        if not self._prepared:
            self.prepare_for_solving()

            # Collect all stamping component instances and current-returning
            # components in the circuit, including those provided by helpers.
            for comp in self.component:
                if comp.stamps():
                    self._stamping_components.append(comp)
            for comp in list(self.component) + list(self.circuit.component_not_added.values()):
                if comp.returns_current():
                    self._current_components.append(comp)

            self._prepared = True

        self.ctx.x = np.zeros(self.N, dtype=complex) # initial guess for solution vector, used for nonlinear iteration

        times = 0
        n_times = 1 # number of iterations to perform before checking for convergence
        while not converged:
            self.ctx.Y = self.zero_MNA_matrix(self.N)
            self.ctx.z = self.zero_RHS(self.N)
            self.stamp(self.ctx)
            self.x_prev = self.ctx.x
            self.ctx.x = self.solve_matrix_equation()
            if return_real:
                self.ctx.x = np.real(self.ctx.x)
            if self.has_nonlinear_components():
                times += 1
                if times >= n_times:
                    converged = self.check_convergence()
            else:
                converged = True
        voltages = self.extract_node_voltages()
        currents = self.extract_currents()
        if os.environ.get("IMPULSO_DEBUG", '0') == '1':
            print("Y-matrix:\n", self.ctx.Y,"\n")
            print("x-vector:\n", self.ctx.x, "\n")
            print("z-vector:\n", self.ctx.z, "\n")
            self.print_voltages(voltages)
            self.print_currents(currents)
        return voltages, currents


    def print_voltages(self, voltages: Dict[int, complex]):
        print("Node voltages:")
        for node, voltage in voltages.items():
            print(f"Node {node}: {voltage} V")
        print()


    def print_currents(self, currents: Dict[str | Component, complex]):
        print("Currents through components:")
        for comp, current in currents.items():
            if isinstance(comp, Component):
                print(f"Component {comp.id}: {current} A")
        print()


    @cache
    def has_nonlinear_components(self) -> bool:
        """Check if the circuit contains any nonlinear components."""
        for comp in self.all_components():
            if not comp.linear():
                return True
        return False


    def check_convergence(self) -> bool:
        dx = self.ctx.x - self.x_prev
        tol = 1e-6
        err = np.max(np.abs(dx))
        if err >= tol:
            return False
        return True


    def extract_currents(self) -> dict:
        currents = {}
        for comp in self._current_components:
            i = comp.current(self.ctx)
            currents[comp.id] = i # by id
            currents[comp] = i # by Component
        return currents


    def extract_node_voltages(self) -> Dict[int, complex]: # dict node id -> voltage
        '''
        '''
        voltages = {node: self.ctx.x[i] for node, i in self.node_index.items()}
        voltages[self.ground_node] = 0.0
        return voltages


    def solve_matrix_equation(self):
        '''
        '''
        return np.linalg.solve(self.ctx.Y, self.ctx.z)


    def zero_RHS(self, N):
        '''
        '''
        return np.zeros(N, dtype=complex)


    def zero_MNA_matrix(self, N):
        '''
        '''
        return np.zeros((N,N), dtype=complex)


    def assign_node_indices(self) -> Tuple[int, Dict[int,int]]:
        '''
        '''
        # --- Collect nodes ---
        all_nodes = set()
        for comp in self.all_components():
            # Check if this is only a simulation directve,
            # without nodes, that should not be included
            # in the node administration
            try:
                directive = comp.is_directive()
            except AttributeError:
                directive = False
            if not directive:
                all_nodes.update(self.nodes.get(comp,[]))
        if None in all_nodes:
            all_nodes.remove(None)
        # Node administration for the MNA matrix:
        node_list = list(all_nodes - {self.ground_node})
        node_index = {n: i for i, n in enumerate(node_list)} # index from node number into its location in the MNA matrix
        num_nodes = len(node_list)
        return num_nodes, node_index


    def assign_augmented_slots(self, N) -> int:
        '''
        Assign a slot to all components that require one in the
        MNA matrix (voltage sources, VCVS, CCVS, Wires, Inductors, Opamps)
        '''
        for comp in self.all_components():
            if comp.augments():
                self.augm_idx[comp] = N
                N = N + 1
        return N


    def stamp(self, ctx: Context = None):
        for comp in self._stamping_components:
            comp.stamp(ctx)



def _solve_acdc(circuit: Circuit,
               freq: float, # frequency for AC analysis, ignored for DC analysis
               ctx: Context = None
               ) -> Tuple[Dict[int | str, complex], # node voltages
                          Dict[str | Component, complex]]: # currents through components
    '''
    Convenience function to solve a circuit without
    needing to create a Solver_ACDC instance.

    Make sure that if doing an AC analysis, the
    operating point has already been solved and
    the nonlinear components have their admittance
    set for AC analysis, otherwise the results may
    be meaningless.
    '''
    assert ctx is None or isinstance(ctx, Context), "ctx must be an instance of Context or None"
    if ctx is not None:
        if freq > 0:
            assert ctx.analysis_type in (None, Analysis.AC), "Context analysis type must be AC or None for AC analysis"

    circuit.validate()
    solver = Solver_ACDC(circuit)
    return solver.solve(freq)


def solve_dc(circuit: Circuit,
             ctx: Context = None
             ) -> Tuple[Dict[int | str, complex], # node voltages
                        Dict[str | Component, complex]]: # currents through components
    '''
    Convenience function to solve a circuit for DC analysis.
    '''
    if ctx is None:
        ctx = Context()
    ctx.analysis_type = Analysis.DC
    return _solve_acdc(circuit, 0, ctx)


def solve_ac(circuit: Circuit,
             freq: float | List[float]
             ) -> Tuple[Dict[int | str, complex], # node voltages
                        Dict[str | Component, complex]]: # currents through components
    '''
    Convenience function to solve a circuit for AC analysis.
    '''
    all_sources = circuit.all_of_type(PowerSource)
    ac_sources = [src for src in all_sources if src.is_ac()]
    if not ac_sources:
        raise TopologyError("No AC sources found in the circuit. The results may be meaningless.")

    non_linears = set() # all nonlinear components in the circuit
    for comp in circuit.components:
        if not comp.linear():
            non_linears.add(comp)

    if len(non_linears) > 0:
        # First do a operating point analysis
        _, idc = solve_dc(circuit)
        for comp in non_linears:
            comp.set_admittance_for_ac(idc[comp])

    ctx = Context()
    ctx.analysis_type = Analysis.AC

    if isinstance(freq, float):
        # single frequency AC analysis
        return _solve_acdc(circuit, freq, ctx)
    else:
        # AC sweep over multiple frequencies
        results = {}
        for f in freq:
            results[f] = _solve_acdc(circuit, f, ctx)
        return results

