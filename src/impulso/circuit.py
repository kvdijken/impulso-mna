from __future__ import annotations
from typing import Dict, List, Optional, Sequence, Iterable, Type
from collections import defaultdict

from .base import TopologyError, Node
from .sources.source import *
from .components.capacitor import Capacitor
from .components.inductor import MutualInductance
from .components.resistor import Resistor
from .components.array import Array

class Circuit:
    """
    Circuit simulator using Modified Nodal Analysis (MNA).

    Supports arbitrary topologies with resistors and voltage sources.
    """

    nodes: Dict[Component, Tuple[Node, ...]]  # component -> connected nodes
    components: list[Component]  # component_id -> Component instance


    def __init__(self, ground_node=0):
        """Initialize an empty circuit."""
        self.components = []
        self.component_not_added = {}
        self.nodes = {}
        self.ground_node = self._proper_node(ground_node)
        self._prepared = False


    def _proper_node(self, node: str | int) -> Node:
        return node


    def __getitem__(self, id: str) -> Optional[Component]:
        for c in self.components:
            if c.id == id:
                return c
        return None


    def __str__(self):
        lines = [
            f"Circuit with {len(self.components)} components "
            f"and {self.num_nodes()} nodes:"
        ]
        lines.append(f"Ground at {self.ground_node.__repr__()}")

        for comp in self.components:
            nodes = self.nodes.get(comp,None)
            if nodes:
                lines.append(
                    f"  {comp} ({comp.__repr__()}) @ {nodes}")
            else:
                lines.append(
                    f"  {comp} ({comp.__repr__()})"
            )
        lines.append("")

        return "\n".join(lines)

    def __repr__(self):
        return (
            f"Circuit("
            f"components={self.components!r}, "
            f"nodes={self.nodes!r}"
            f")"
        )

    def num_nodes(self):
        return len(
            set(
                node
                for nodes in self.nodes.values()
                for node in nodes
            )
        )

    def all_non_ground_nodes(self) -> set:
        '''
        Returns a set of all nodes except
        ground in the circuit.
        '''
        return {
            node
            for connected_nodes in self.nodes.values()
            for node in connected_nodes
            if node != self.ground_node
        }

    def add(self,
            comp: Component,
            nodes: List[int | str]
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


        # convert to the proper Node type
        _nodes: Tuple[Node,...] = tuple([self._proper_node(n) for n in nodes])
        try:
            do_add = comp.before_add(self, _nodes)
        except AttributeError:
            do_add = True

        if do_add:
            check()
            self.components.append(comp)
            self.nodes[comp] = _nodes
        else:
             self.component_not_added[comp.id] = comp

        return self


    def add_array(
        self,
        array: Array,
        nodes: Sequence[Sequence[Node]]
    ) -> None:

        if len(nodes) != len(array.components):
            raise ValueError(
                f"Expected {len(array.components)} node lists, "
                f"got {len(nodes)}"
            )

        for i, component_nodes in enumerate(nodes):
            self.add(array[i], list(component_nodes))


    def shunt(
        self,
        array: Array,
        nodes: Iterable[Node]
    ) -> None:
        self.add_array(
            array,
            [[node, self.ground_node] for node in nodes]
        )


    def gshunt(self,
               g: float,
               id_prefix: Optional[str]=None) -> None:
        '''
        Constructs shunt conductances between every node
        in the circuit and ground.

        Note that this method may create duplicate id's
        if called twice with id_prefix is None. When
        calling more than once, use custom prefix.
        '''
        nodes = self.all_non_ground_nodes()
        array = Array(Resistor,
                      n=len(nodes),
                      resistance=1/g,
                      id_prefix=id_prefix if id_prefix else 'gshunt_')
        self.shunt(array, nodes)


    def cshunt(self,
               c: float,
               id_prefix: Optional[str]=None) -> None:
        '''
        Constructs shunt capacitances between every node
        in the circuit and ground.

        Note that this method may create duplicate id's
        if called twice with id_prefix is None. When
        calling more than once, use custom prefix.
        '''
        nodes = self.all_non_ground_nodes()
        array = Array(Capacitor,
                      n=len(nodes),
                      capacitance=c,
                      id_prefix=id_prefix if id_prefix else 'cshunt_')
        self.shunt(array, nodes)


    def add_instruction(self, instruction: Component):
#        assert(isinstance(instruction, MutualInductance))
        try:
            do_add = instruction.before_add(self, ())
        except AttributeError:
            do_add = True
        if do_add:
            self.components.append(instruction)
        return self


    def all_nodes(self) -> List[Node]:
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

    def all_of_type(self, _type: Type[CircuitItem]) -> Sequence[CircuitItem]:
        result = [c for c in self.components if isinstance(c, _type)]
        return result

    def validate(self):
        if not self.ground_node in self.all_nodes():
            raise TopologyError(f"Ground node {self.ground_node} is not connected to any component in the circuit.")
        if len(self.components) == 0:
            raise TopologyError("Circuit must contain at least one component.")



