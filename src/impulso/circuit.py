import numpy as np
from typing import Dict, List, Tuple, Optional, Type, Any

from .sources.source import *
from .components.inductor import MutualInductance


class Circuit:
    """
    Circuit simulator using Modified Nodal Analysis (MNA).

    Supports arbitrary topologies with resistors and voltage sources.
    """

    nodes: Dict[Component, List[int]]  # component -> connected nodes
    component: Dict[str, Component]  # component_id -> Component instance

    
    def __init__(self, ground_node =0):
        """Initialize an empty circuit."""
        self.component = {}
        self._node_voltage_cache: Optional[Dict[int, float]] = None
        self._comp_currents_cache: Optional[Dict[str, float]] = None
        self._topology_hash: Optional[str] = None
        self.nodes = {}
        self.ground_node = ground_node


    def __getitem__(self, component_id: str) -> Component:
        return self.component[component_id]
    
    
    def add(self, 
            component: Component, 
            nodes: List[int]
            ) -> 'Circuit':
        """ Add a component to the circuit. """
        
        def check():
            """ Perform checks on the component and nodes before adding to the circuit. """
            # TODO: Add checks for valid node indices, duplicate component IDs, etc.
            assert(not isinstance(component, MutualInductance))
            
            # Duplicate ID check
            assert(self.component.get(component.id) is None), f"Component ID {component.id} already exists in the circuit."
            
            assert(isinstance(component, Component)), f"Expected component to be an instance of Component, got {type(component)}"

        try:
            do_add, current = component.before_add(self, nodes)
        except AttributeError:
            do_add = True
            
        if do_add:
            check()        
            self.component[component.id] = component
            self.nodes[component] = nodes
        elif current:
            self.component[component.id] = component

        return self


    def add_instruction(self, instruction: Component):
        assert(isinstance(instruction, MutualInductance))
        self.component[instruction.id] = instruction
        return self
        
        
    def all_nodes(self) -> List[int]:
        """Return a sorted list of all nodes in the circuit."""
        _nodes = set()
        for c in self.component.values():
            _nodes.update(self.nodes.get(c, [])) # A component may not have been added to the circuit itself, only its sub-components (e.g. NPN's internal components) 
        if None in _nodes:
            _nodes.remove(None)
        # _nodes may be strings or int's
        # split in str and int nodes, sort separately and concatenate
        _nodes_str = sorted([n for n in _nodes if isinstance(n, str)])
        _nodes_int = sorted([n for n in _nodes if isinstance(n, int)])
        
        return _nodes_int + _nodes_str
    
    def all_of_type(self, _type: CircuitItem) -> List[CircuitItem]:
        all = [c for c in self.component.values() if isinstance(c, _type)]
        return all

    def validate(self):
        # TODO Check if there is a component connected to ground
        pass
    
    
