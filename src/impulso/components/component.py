from typing import Dict, List, Tuple, Optional, Type, Any, Callable
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
    x: NDArray[complex] # previous solution vector (node voltages)
    Y: NDArray[complex] # augmented admittance matrix
    z: NDArray[complex] # RHS vector

    # query index into admittance matrix for a given circuit item
    idx_query_fn: Callable[[CircuitItem |     # query circuit item
                            int |             # query node
                            list[int] |       # query list of nodes
                            Tuple[int, ...]], # query tuple of nodes
                           Tuple[int, ...]]   # returns list of indices into admittance matrix

    # query augmentation index for a given circuit item (if it augments the system)
    augm_query_fn: Callable[CircuitItem, int]

    # query nodes of a circuit item (e.g. component)
    nodes_query_fn: Callable[CircuitItem, Tuple[int, ...]]

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

    def stamps(self) -> bool:
        return True

    def returns_current(self) -> bool:
        """Whether this component can return a current when queried."""
        return True
    
    def linear(self) -> bool:
        return True

    @abc.abstractmethod
    def stamp(self, ctx: Context):
        pass

    @abc.abstractmethod
    def current(self, ctx: Context) -> complex:
        pass

    def before_add(self,
                   circuit: 'Circuit',
                   nodes: List[int]
                   ) -> Tuple[bool, bool]:
        #                     ^add  ^current
        """
        Hook called before adding to circuit. Can be used to modify the circuit.

        Returns:
            tuple of:

            should_add_component: whether the component itself should be added to the circuit
            (e.g. for a BJT, we do NOT add the BJT component itself, but its internal resistors,
            diodes and capacitors).

            should_add_current: whether the component can return a current (e.g. for a BJT,
            we want to be able to query the collector current from the BJT component itself,
            not from its internal components).
        """
        return True, True


class CompoundComponent(Component):
    """
    A component that contains other components (e.g. subcircuit).
    """
    pass

