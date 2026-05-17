from __future__ import annotations
from typing import Dict, List, Optional

from .base import TopologyError
from .sources.source import *
from .components.inductor import MutualInductance


class Circuit:
    """
    Circuit simulator using Modified Nodal Analysis (MNA).

    Supports arbitrary topologies with resistors and voltage sources.
    """

    nodes: Dict[Component, List[int]]  # component -> connected nodes
    components: list[Component]  # component_id -> Component instance


    def __init__(self, ground_node =0):
        """Initialize an empty circuit."""
        self.components = []
        self.component_not_added = {}
        self._node_voltage_cache: Optional[Dict[int, float]] = None
        self._comp_currents_cache: Optional[Dict[str, float]] = None
        self._topology_hash: Optional[str] = None
        self.nodes = {}
        self.ground_node = ground_node
        self._prepared = False


    def __getitem__(self, id: str) -> Component:
        for c in self.components:
            if c.id == id:
                return c
        return None


    def add(self,
            comp: Component,
            nodes: List[int]
            ) -> Circuit:
        """ Add a component to the circuit. """

        def check():
            """ Perform checks on the component and nodes before adding to the circuit. """
            if not isinstance(comp, Component):
                raise TypeError(f"Expected component to be an instance of Component, got {type(comp)}")

            if not (isinstance(nodes, list)):
                raise TypeError(f"Expected nodes to be a list, got {type(nodes)}")

            assert(not isinstance(comp, MutualInductance))

            # Duplicate ID check
            for c in self.components:
                if c.id == comp.id:
                    raise TopologyError(f"Component ID {comp.id} already exists in the circuit.")

            # Node connection check, at least 2 nodes
            if len(nodes) < 2:
                raise ValueError(f"Component {comp.id} must be connected to at least 2 nodes, got {len(nodes)}")


        try:
            do_add = comp.before_add(self, nodes)
        except AttributeError:
            do_add = True

        if do_add:
            check()
            self.components.append(comp)
            self.nodes[comp] = nodes
        else:
             self.component_not_added[comp.id] = comp

        return self


    def add_instruction(self, instruction: Component):
#        assert(isinstance(instruction, MutualInductance))
        try:
            do_add = instruction.before_add(self, [])
        except AttributeError:
            do_add = True
        if do_add:
            self.components.append(instruction)
        return self


    def all_nodes(self) -> List[int]:
        """Return a sorted list of all nodes in the circuit."""
        _nodes = set()
        for c in self.components:
            _nodes.update(self.nodes.get(c, [])) # A component may not have been added to the circuit itself, only its sub-components (e.g. NPN's internal components)
        if None in _nodes:
            _nodes.remove(None)
        # _nodes may be strings or int's
        # split in str and int nodes, sort separately and concatenate
        _nodes_str = sorted([n for n in _nodes if isinstance(n, str)])
        _nodes_int = sorted([n for n in _nodes if isinstance(n, int)])

        return _nodes_int + _nodes_str

    def all_of_type(self, _type: CircuitItem) -> List[CircuitItem]:
        all = [c for c in self.components if isinstance(c, _type)]
        return all

    def validate(self):
        if not self.ground_node in self.all_nodes():
            raise TopologyError(f"Ground node {self.ground_node} is not connected to any component in the circuit.")
        if len(self.components) == 0:
            raise TopologyError("Circuit must contain at least one component.")


