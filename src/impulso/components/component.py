from typing import Dict, List, Tuple, Optional, Type, Any
import uuid
import abc
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ..base import Analysis

LARGE_CONDUCTANCE = 1e12



class CircuitItem(abc.ABC):
    """Base class for items in the circuit (components and instructions)."""
    
    def __init__(self, id: Optional[str] = None):
        self.id = id or uuid.uuid4().hex

    
class Context():
    ground_node: int
    analysis_type: Analysis
    x: NDArray[np.complex] # previous solution vector (node voltages)
    Y: NDArray[np.complex] # augmented admittance matrix
    z: NDArray[np.complex] # RHS vector

    # query index into admittance matrix for a given circuit item
    idx_query_fn: callable[[CircuitItem |     # query circuit item
                            int |             # query node
                            list[int] |       # query list of nodes
                            Tuple[int, ...]], # query tuple of nodes
                           Tuple[int, ...]]   # returns list of indices into admittance matrix

    # query augmentation index for a given circuit item (if it augments the system)
    augm_query_fn: callable[CircuitItem, int]
    
    # query nodes of a circuit item (e.g. component)
    nodes_query_fn: callable[CircuitItem, Tuple[int, ...]]
    
    # This dataclass can be extended with additional fields as needed.
    #
    # For transient analysis we can add time, dt, previous
    # voltages and currents etc.
    #
    # For AC analysis we can add the complex frequency, etc.

    
class Component(CircuitItem):
    """
    Base class for all circuit components.
    """

    @abc.abstractmethod
    def admittance(self, s: Optional[complex] = None) -> complex:
        """Calculate admittance (1/impedance) for AC analysis."""
        pass
        
    @abc.abstractmethod
    def augments(self) -> None:
        pass
    
    def linear(self) -> bool:
        return True
    
    @abc.abstractmethod
    def stamp(self, ctx: Context):
        pass
    
    @abc.abstractmethod
    def current(self, ctx: Context) -> complex:
        pass
    
    

class CompoundComponent(Component):
    """
    A component that contains other components (e.g. subcircuit).
    """
    
    def before_add(self,
                   circuit: 'Circuit'
                   ) -> Tuple[bool, bool]:
        #                     ^add  ^current
        """Hook called before adding to circuit. Can be used to modify the circuit."""
        return False, True