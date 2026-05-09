from ..components.component import *
from ..components.resistor import Resistor
from ..components.capacitor import Capacitor


class PowerSource(Component):
    """Base class for power sources (voltage and current)."""

    def __init__(self,
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
        voltage: float,
        id: Optional[str] = None,
    ):
        """
        Independent voltage source.

        voltage: V(nodes[0]) - V(nodes[1])
        """
        self.voltage = voltage
        super().__init__(id=id)

    def set_voltage(self, voltage: float):
        self.voltage = voltage

    def admittance(self, s: Optional[complex] = None) -> complex:
        return np.inf  # ideal voltage source has infinite admittance (zero impedance)

    def augments(self):
        return True

    def stamp(self,
              x: Dict[int, float],             # previous node voltages
              Y: Dict[Tuple[int, int], float], # admittance matrix
              z: Dict[int, float],             # RHS vector
              s: complex = 0                   # complex frequency
              ):
        pass

    def current(self,
                x: Dict[int, float], # solution vector
                idx_query_fn: callable # function to query indices
                ) -> complex:
        pass



