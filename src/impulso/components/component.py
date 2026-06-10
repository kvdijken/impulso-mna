from __future__ import annotations
from typing import List, Protocol, Tuple, Optional, Callable, TYPE_CHECKING
import uuid
import abc

import numpy as np
from numpy.typing import NDArray

from ..base import Analysis

if TYPE_CHECKING:
    from ..circuit import Circuit


LARGE_CONDUCTANCE = 1e12


class Stamper(Protocol):
    def stamp(self,
              circuit: Circuit,
              ctx: Context):
        ...


class CircuitItem(abc.ABC):
    """Base class for items in the circuit (components and instructions)."""

    def __init__(self, id: Optional[str] = None):
        self.id = id or uuid.uuid4().hex

    def __str__(self) -> str:
        return self.id

    def __repr__(self) -> str:
        try:
            value = self.__value__()
            _type_name = self.__component_typename__()
            if value is None:
                return _type_name
            else:
                if not isinstance(value,str):
                    value = str(value)
                return _type_name + "=" + value
        except:
            return self.__str__()

    def __component_typename__(self) -> str:
        return self.__class__.__name__

    def init_state(self) -> None:
        """Initialize any internal state for transient analysis."""
        pass

    def initialize_transient_state(self, ctx: Context) -> None:
        """Initialize any internal state for transient analysis based on the context."""
        pass

    def update_state(self, ctx: Context) -> None:
        """Update internal state based on current solution for transient analysis."""
        pass


class Context():
    ground_node: int
    analysis_type: Analysis
    x: NDArray[np.complex128] # previous solution vector (node voltages)
    Y: NDArray[np.complex128] # augmented admittance matrix
    z: NDArray[np.complex128] # RHS vector

    # query index into admittance matrix for a given circuit item
    idx_query_fn: Callable[[CircuitItem |     # query circuit item
                            int |             # query node
                            list[int] |       # query list of nodes
                            Tuple[int, ...]], # query tuple of nodes
                           Tuple[int, ...]]   # returns list of indices into admittance matrix

    # query augmentation index for a given circuit item (if it augments the system)
    augm_query_fn: Callable[[CircuitItem], int]

    # query nodes of a circuit item (e.g. component)
    nodes_query_fn: Callable[[CircuitItem], Tuple[int, ...]]

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

    def __repr__(self) -> str:
        value = self.__value__()
        _type_name = self.__component_typename__()
        if value is None:
            return _type_name
        else:
            if not isinstance(value,str):
                value = str(value)
            return _type_name + "=" + value

    @abc.abstractmethod
    def __value__(self) -> str | None:
        ...

    @abc.abstractmethod
    def admittance(self, s: Optional[complex] = None) -> complex:
        """Calculate admittance (1/impedance) for AC analysis."""
        pass

    def augments(self, ctx: Context) -> bool:
        return False

    def stamps(self) -> bool:
        """Whether this component stamps itself into the admittance matrix."""
        return True

    def returns_current(self) -> bool:
        """Whether this component can return a current when queried."""
        return True

    def linear(self) -> bool:
        return True

    @abc.abstractmethod
    def current(self, ctx: Context) -> complex:
        pass

    def before_add(self,
                   circuit: Circuit,
                   nodes: List[int]
                   ) -> bool:
        """
        Hook called before adding to circuit. Can be used to modify the circuit.

        Returns:
            should_add_component: whether the component itself should be added to the circuit
            (e.g. for a BJT, we do NOT add the BJT component itself, but its internal resistors,
            diodes and capacitors).
        """
        return True


class CompoundComponent(Component):
    """
    A component that contains other components (e.g. subcircuit).
    """
    pass

