import os

from typing import Dict, List, Tuple
import numpy as np
from functools import cache
from dataclasses import dataclass

from .base import Analysis, TopologyError
from .components.component import Component, Context
from .circuit import Circuit
from .sources.source import PowerSource
from .helperregistry import registry, StampingHelper


@dataclass
class Statistics():
    solves: int = 0
    singulars: int = 0
    dc_analysis: int = 0
    ac_analysis: int = 0
    not_converged: int = 0

class StatisticsScope():

    def __init__(self,
                 show: bool,
                 stats: Statistics = None):
        self._owning = not stats
        self._show = show
        if self._owning:
            self._stats = Statistics()
        else:
            self._stats = stats

    def print_statistics(self):
        print("\nStatistics:")
        print(f"Number of matrix solves: {self._stats.solves}")
        print(f"Number of singular matrices: {self._stats.singulars}")
        print(f"Number of DC analyses: {self._stats.dc_analysis}")
        print(f"Number of AC analyses: {self._stats.ac_analysis}")
        print(f"Number of re-solve because of not converged system: {self._stats.not_converged}")

    def __enter__(self):
        return self._stats

    def __exit__(self, exc_type, exc, tb):
        if self._show and self._owning:
            self.print_statistics()
        return False


class Solver_ACDC():

    nodes: Dict[Component, List[int]]  # component -> connected nodes
    components: list[Component]  # component_id -> Component instance
    node_index: Dict[int, int] = {} # node number -> index in MNA matrix
    ground_node: int = 0
    augm_idx: Dict[Component, int] = {} # component -> index in MNA matrix for
                                        # augmented variables (currents through
                                        # voltage sources, etc.)

    def __init__(self,
                 circuit: Circuit):
        circuit.validate()
        self.circuit = circuit
        self._prev_analysis_type = None
        self.initialize()
        self._stats = None


    def initialize(self):
        self._prepared = False
        self.nodes = self.circuit.nodes
        self.components = self.circuit.components
        self.ground_node = self.circuit.ground_node
        self.x_prev = None # previous solution vector, used for nonlinear iteration
        self._stamping_components = [] # components that need to be stamped in the MNA matrix (e.g. voltage sources, inductors, opamps, etc.)
        self._current_components = [] # components for which we want to extract currents after solving (e.g. voltage sources, inductors, opamps, etc.)


    def create_context(self, freq: float | None) -> Context:
        ctx = Context()
        match freq:
            case None | 0.0 | 0:
                ctx.analysis_type = Analysis.DC
                ctx.s = 0
            case _:
                ctx.analysis_type = Analysis.AC
                ctx.s = 1j * 2 * np.pi * freq
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


    def _reset_cache(self):
        self.get_nodes.cache_clear()
        self.get_augm_index.cache_clear()
        self.get_node_indices.cache_clear()
        self.has_nonlinear_components.cache_clear()


    def solve(self,
              freq: float,
              show_output: bool = False,
              stats: Statistics = None
              ) -> Tuple[Dict[int | str, complex], # node voltages
                         Dict[str | Component, complex]]: # currents through components
        """
        Solve the circuit for the given frequency and ground node.

        Returns:
            voltages: dict node -> complex voltage
            currents: dict comp_id | component -> complex current
        """
        self._show_output = show_output
        self._stats = stats
        self.ctx = self.create_context(freq)
        self.node_administration()
        return self.solve_mna(freq)


    def show_output(self) -> bool:
        return self._show_output


    def node_administration(self):
        # Must be called after change of analysis type, since some components may be
        # included/excluded from the node administration for certain analysis types.
        self.N, self.node_index = self.assign_node_indices()
        self.N = self.assign_augmented_slots(self.N)
        if (self.ctx.analysis_type != self._prev_analysis_type) and self.show_output():
            self._prev_analysis_type = self.ctx.analysis_type
            print(f"Node administration complete.")
            print(f"Ground node: {self.ground_node}")
            print(f"Number of components: {len(self.components)}")
            print(f"Number of non-linear components: {self.number_of_non_linear_components()}")
            print(f"Number of nodes (excluding ground): {len(self.node_index)}")
            print(f"Total size of MNA matrix: {self.N}")


    def number_of_non_linear_components(self):
        n = 0
        for comp in self.components:
            if not comp.linear():
                n += 1
        return n


    def all_nodes(self) -> List[int]:
        """Return a list of all nodes in the circuit."""
        return self.node_index.keys()


    def prepare_for_solving(self) -> None:
        # Prepare the circuit for solving

        # Get all the stamping helpers
        for name, factory in registry.factories(cls=StampingHelper):
            stamping_helper = factory.create_helper(self.circuit, self.ctx)
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
        if self._stats:
            if freq == 0:
                self._stats.dc_analysis += 1
            else:
                self._stats.ac_analysis += 1

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
            for comp in self.components:
                if comp.stamps():
                    self._stamping_components.append(comp)
            for comp in list(self.components) + list(self.circuit.component_not_added.values()):
                if comp.returns_current():
                    self._current_components.append(comp)

            self._prepared = True

        self.ctx.x = np.zeros(self.N, dtype=complex) # initial guess for solution vector, used for nonlinear iteration

        times = 0
        n_times = 1 # number of iterations to perform before checking for convergence
        while not converged:
            self.ctx.Y = self.zero_MNA_matrix(self.N)
            self.ctx.z = self.zero_RHS(self.N)
            self.stamp()
            self.x_prev = self.ctx.x
            self.ctx.x = self.solve_matrix_equation()
            if return_real:
                self.ctx.x = np.real(self.ctx.x)
            if self.has_nonlinear_components():
                times += 1
                if times >= n_times:
                    converged = self.check_convergence()
                    if self._stats and not converged:
                        self._stats.not_converged += 1
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
        for comp in self.components:
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
        if self._stats:
            self._stats.solves += 1
        try:
            return np.linalg.solve(self.ctx.Y, self.ctx.z)
        except np.linalg.LinAlgError as e:
            if self._stats:
                self._stats.singulars += 1
            raise e



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
        for comp in self.components:
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
        self.augm_idx = {}
        for comp in self.components:
            if comp.augments(self.ctx):
                self.augm_idx[comp] = N
                N = N + 1
        return N


    def stamp(self):
        for comp in self._stamping_components:
            comp.stamp(self.ctx)


def solve_dc(circuit: Circuit,
             show_output: bool = False,
             stats: Statistics = None
             ) -> Tuple[Dict[int | str, complex], # node voltages
                        Dict[str | Component, complex]]: # currents through components
    '''
    Convenience function to solve a circuit for DC analysis.
    '''
    solver = Solver_ACDC(circuit)
    with StatisticsScope(show_output,stats) as _stats:
        return solver.solve(freq=0, show_output=show_output, stats=_stats)


def solve_ac(circuit: Circuit,
             freq: float | List[float],
             show_output: bool = False,
             stats: Statistics = None
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

    solver = Solver_ACDC(circuit)
    with StatisticsScope(show=show_output, stats=stats) as _stats:
        if show_output:
            print("\nPerforming DC operating point analysis:")
        if len(non_linears) > 0:
            # First do a operating point analysis
            _, idc = solver.solve(freq=0, show_output=show_output, stats=_stats)
            for comp in non_linears:
                comp.set_admittance_for_ac(idc[comp])

        if isinstance(freq, float):
            # single frequency AC analysis
            if show_output:
                print("\nPerforming single frequency AC analysis:")
            results = solver.solve(freq=freq, show_output=show_output, stats=_stats)
        else:
            # AC sweep over multiple frequencies
            results = {}
            if show_output:
                print("\nPerforming frequency range AC analysis:")
            first = True
            for f in freq:
                results[f] = solver.solve(freq=f, show_output=show_output and first, stats=_stats)
                first = False

    return results


