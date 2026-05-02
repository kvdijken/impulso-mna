from typing import Dict, List, Tuple, Optional, Type, Any
import numpy as np
import logging
from collections import defaultdict
from functools import cache

from .base import Analysis
from .components.component import Component, Context
from .circuit import Circuit


class Stamper():
    ''' 
    A simple stamper class that iterates through
    all components and calls their stamp method.
    
    More clever methods may be invented and
    implemented in subclasses, for example to only
    stamp a subset of components in each iteration, or to
    stamp components in a certain order.
    
    The Stamper class is separate from the Solver_ACDC
    class to allow for different stamping strategies
    without needing to modify the core solver logic.
    
    The Stamper subclasses can be injected into
    Solver_ACDC via its constructor, or via set_stamper(),
    allowing for flexible stamping strategies
    '''
    
    def __init__(self, solver: 'Solver_ACDC'):
        self.solver = solver

    def stamp(self, ctx: Context):
        for comp in self.solver.all_components():
            comp.stamp(ctx)
        

class Stamper_NonLinearOnly(Stamper):
    ''' 
    A stamper that only stamps nonlinear components, which can be useful for
    iterative nonlinear solvers where the linear components do not change 
    between iterations.
    
    The stamper can be reset to stamp the linear components again if needed.
    
    Users of this class must take care to call reset() if they want to stamp
    the linear components again.
    '''
    
    non_linear_components: List[Component]
    first_stamp: bool
    
    def __init__(self, solver: 'Solver_ACDC'):
        self.solver = solver
        self.non_linear_components = [comp 
                                      for comp in self.solver.all_components() 
                                      if not comp.linear()]
        self.first_stamp = True

    def stamp(self, ctx: Context):
        if self.first_stamp:
             # Stamp linear components only in the first iteration
            for comp in self.solver.all_components():
                if comp.linear():
                    comp.stamp(ctx)
            self.Y_linear = ctx.Y.copy() # save the stamped linear part of the MNA matrix  
            self.z_linear = ctx.z.copy() # save the stamped linear part of the RHS vector
            self.first_stamp = False
        else:
             # Restore the stamped linear part of the MNA matrix and RHS vector
            ctx.Y[:] = self.Y_linear
            ctx.z[:] = self.z_linear            
        for comp in self.non_linear_components:
            comp.stamp(ctx)

    def reset(self):
        self.first_stamp = True
        

class Solver_ACDC():

    all: Dict[Type[Component], List[Component]] = {} # sorted catalog of components by type
    nodes: Dict[Component, List[int]]  # component -> connected nodes
    component: Dict[str, Component]  # component_id -> Component instance  
#    ground_node: int | str
    node_index: Dict[int, int] = {} # node number -> index in MNA matrix
#    Y: Any # augmented MNA matrix
#    z: Any # augmented MNA RHS vector
#    x: Any # solution vector from MNA solver
    ground_node: int = 0
#    s: complex # complex frequency for AC analysis
    augm_idx: Dict[Component, int] = {} # component -> index in MNA matrix for 
                                        # augmented variables (currents through 
                                        # voltage sources, etc.)
    reuse_solution: bool # whether to reuse the solution from the previous
                         # solve as the initial guess for the next solve,
                         # which can speed up convergence for nonlinear
                         # circuits when sweeping over frequencies or other parameters

    def __init__(self,
                 nodes: Dict[Component, List[int]], 
                 component: Dict[str, Component],
                 ground_node: int | str,
                 reuse_solution: bool = True
                 ):
        self.nodes = nodes
        self.component = component
        self.ground_node = ground_node
        self.stamper = None
        self.reuse_solution = reuse_solution
        self.x_prev = None # previous solution vector, used for nonlinear iteration
        self.debug = False
        self.ctx = self.create_context()


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
#        return [self.node_index.get(n, None) for n in self.nodes[comp]]
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
        return self.component.values()
    
    
    def all_component_types(self) -> List[Type[Component]]:
        '''Return a list of all component types in the circuit.'''
        types = set()
        for c in self.all_components():
            types.add(type(c))
        return list(types)
    
    
    def node_administration(self):
        # --- Separate components ---
        self.all = {} # dict component_type -> list of components of that type
        self.all = defaultdict(list)
        for comp in self.all_components():
            self.all[type(comp)].append(comp)
    
        self.N, self.node_index = self.assign_node_indices()
        self.N = self.assign_augmented_slots(self.N)
    
    
    def all_nodes(self) -> List[int]:
        """Return a list of all nodes in the circuit."""
        return self.node_index.keys()
    
    
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
        try:
            return self._solve_mna(freq, return_real)
        except Exception as e:
            if self.reuse_solution:
                if self.debug:
                    print("Warning: MNA solve failed, retrying without reusing previous solution as initial guess. Error message:", e)
                # If the solve fails, reset the previous solution to None
                # to avoid using a potentially bad initial guess in the next solve.
                self.x_prev = None
                for comp in self.all_components():
                    if hasattr(comp, 'reset'):
                        comp.reset()
                        
                # Try again without reusing the previous solution, which can help
                # if the previous solution was a bad initial guess for the nonlinear solver.
                return self._solve_mna(freq, return_real)
            else:
                raise e
                
                
    def _solve_mna(self,
                   freq: float = 0,
                   return_real: bool = False
                   ) -> Tuple[Dict[int, complex], 
                              Dict[str | Component, complex]]:
        converged = False

        if self.stamper is None:
            self.stamper = Stamper(self)

#        self.ensure_context(freq) # make sure that there is a context
        self.ctx.s = 1j * 2 * np.pi * freq
        if self.ctx.analysis_type is None:
            self.ctx.analysis_type = Analysis.AC if freq != 0 else Analysis.DC
        
        # Set up the intial solution vector. This is used
        # for nonlinear iteration, and can be reused from
        # the previous solve if desired (reuse_solution == True).
        if self.reuse_solution and self.x_prev is not None:
            self.ctx.x = self.x_prev
        else:
            self.ctx.x = np.zeros(self.N, dtype=complex) # initial guess for solution vector, used for nonlinear iteration
            
        times = 1
        n_times = 1 # number of iterations to perform before checking for convergence
        while not converged:
            self.ctx.Y = self.zero_MNA_matrix(self.N)
            self.ctx.z = self.zero_RHS(self.N)
            self.stamper.stamp(self.ctx)
            self.x_prev = self.ctx.x
            self.ctx.x = self.solve_matrix_equation()
            if return_real:
                self.ctx.x = np.real(self.ctx.x)
            if self.has_nonlinear_components():
                if times >= n_times:
                    converged = self.check_convergence()
                else:
                    times += 1
            else:
                converged = True
        voltages = self.extract_node_voltages()
        if self.debug:
            self.print_voltages(voltages)
        currents = self.extract_currents()                
        if self.debug:
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
    
    
    def voltage_indices(self) -> List[int]:
        """Return the indices of the voltage variables in the MNA solution vector."""
        return list(self.node_index.values())
    
    
    def current_indices(self) -> List[int]:
        """Return the indices of the current variables in the MNA solution vector."""
        return list(self.augm_idx.values())
    
    
    def check_convergence(self) -> bool:
        if False:
            v_tol = 1e-6
            v_indices = self.voltage_indices()
            arr = (self.x - x_prev)[v_indices]
            v_err = np.linalg.norm(arr)
            if v_err >= v_tol:
                return False

            i_tol = 1e-6
            i_indices = self.current_indices()
            arr = (self.x - x_prev)[i_indices]
            i_err = np.linalg.norm(arr)
            if i_err >= i_tol:
                return False
        else:
            dx = self.ctx.x - self.x_prev
            tol = 1e-6
            err = np.max(np.abs(dx))
            if err >= tol:
                return False

        return True
    
    
    def extract_currents(self) -> dict:
        currents = {}
        for comp in self.all_components():
            currents[comp.id] = comp.current(self.ctx)
            # Make currents available by id and by component reference
            currents[comp] = currents[comp.id]
        return currents


    def extract_node_voltages(self) -> Dict[int, complex]: # dict node id -> voltage
        '''
        '''
        if True:
#            voltages = {node: self.x[self.node_index[node]] for node in self.node_index.keys()}
            voltages = {node: self.ctx.x[i] for node, i in self.node_index.items()}
            voltages[self.ground_node] = 0.0
        else:
            voltages = {self.ground_node: 0.0}
            for node in self.node_index.keys():
                voltages[node] = self.x[self.node_index[node]]
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
    
    
    def list_of_all(self, component_type):
        '''
        Return a list of all components of the given type in the circuit.
        '''
        return [c for c in self.all_components() 
                if isinstance(c, component_type)]


    @cache
    def indices(self,
                query: List[int] | Component | int,
                nodes = False,
                augm = True
                ) -> List[int] | int | None:
        '''
        Return the indices of 
        - the circuit nodes (if query is a list of node numbers).
          For a ground node, None is returned.
        - the component (if query is a Component instance)
        '''
        # Make sure query is a [int] or a Component instance
        if isinstance(query, int):
            query = [query]
        elif isinstance(query, tuple):
            query = list(query)
            
        if isinstance(query, list):
            return [self.node_index.get(n, None) for n in query]
        
        elif isinstance(query, Component):
            
            nodes = nodes or not query.augments() # if not augments, then we want node indices by default
            if nodes:
                idx = self.get_node_indices(query)
            augm = augm and query.augments()
            if augm:
                augm_idx = self.augm_idx[query]
            if nodes and augm:
                return idx, augm_idx
            elif nodes:
                return idx
            elif augm:
                return augm_idx
        return None


    def stamp(self, ctx: Context = None):
        for comp in self.all_components():
            comp.stamp(ctx)


    def node_voltages(self, comp: Component) -> Tuple[complex, complex]:
        '''
        Return the voltages at the nodes connected to the given component.
        If a node is the ground node, return 0 for its voltage.
        '''
        i1, i2 = self.get_node_indices(comp)
        if i1 is None:
            v1 = 0.0
        else:
            v1 = self.ctx.x[i1]
        if i2 is None:
            v2 = 0.0
        else:
            v2 = self.ctx.x[i2]
        return v1, v2
    
    
def _solve_acdc(circuit: Circuit,
               freq: float, 
               ctx: Context = None
               ) -> Tuple[Dict[int | str, complex], # node voltages
                          Dict[str | Component, complex]]: # currents through components
    '''
    Convenience function to solve a circuit without
    needing to create a Solver_ACDC instance.
    '''
    solver = Solver_ACDC(circuit.nodes, circuit.component, circuit.ground_node)
    return solver.solve(freq)


def solve_dc(circuit: Circuit,
             aux = None
             ) -> Tuple[Dict[int | str, complex], # node voltages
                        Dict[str | Component, complex]]: # currents through components
    '''
    Convenience function to solve a circuit for DC analysis.
    '''
    return _solve_acdc(circuit, 0, aux)


def solve_ac(circuit: Circuit,
             freq: float, 
             ctx: Context = None
             ) -> Tuple[Dict[int | str, complex], # node voltages
                        Dict[str | Component, complex]]: # currents through components
    '''
    Convenience function to solve a circuit for AC analysis.
    '''
    # TODO Check is there is at least one AC source in the circuit, and if not, raise a warning that the results may be meaningless since there is no excitation at the given frequency.
    if ctx is None:
        ctx = Context()
    ctx.analysis_type = "AC"
    return _solve_acdc(circuit, freq, ctx)

