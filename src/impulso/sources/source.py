import abc

from quantiphy import Quantity

from ..components.component import *


class PowerSource(Component):
    """Base class for power sources (voltage and current)."""

    def __init__(self, *,
                 ac_source: bool = False,
                 id: Optional[str] = None):
        self.id = id or uuid.uuid4().hex
        self.ac_source = ac_source

    def is_ac(self) -> bool:
        """Return True if this source is an AC source."""
        return self.ac_source


class VoltageSource(PowerSource):

    def __init__(
        self,
        *,
        voltage: float,
        id: Optional[str] = None,
    ):
        """
        Independent voltage source.

        voltage: V(nodes[0]) - V(nodes[1])
        """
        self.voltage = voltage
        super().__init__(id=id)

    def __value__(self) -> str | None:
        return Quantity(self.voltage,"V").render(form="si",spacer="")

    def set_voltage(self, voltage: float):
        self.voltage = voltage

    def augments(self, ctx: Context):
        return True

    @abc.abstractmethod
    def stamp(self,
              x: Dict[int, float],             # previous node voltages
              Y: Dict[Tuple[int, int], float], # admittance matrix
              z: Dict[int, float],             # RHS vector
              s: complex = 0                   # complex frequency
              ):
        pass

    @abc.abstractmethod
    def current(self,
                x: Dict[int, float], # solution vector
                idx_query_fn: callable # function to query indices
                ) -> complex:
        pass



