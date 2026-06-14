from typing import Tuple, Optional

from .source import PowerSource
from ..components.component import Context
from ..base import Node

class VCCS(PowerSource):
    """
    Voltage controlled current source.
    Connect as [out-, out+, in-, in+], where current flows from out- to out+
    Connect to voltage controlling nodes with the connect() method.

    Current flows from nodes[0] → nodes[1].
    Control voltage is defined as V(vnodes[1]) - V(vnodes[0]).
    Current = gm * control_voltage
    """
    def __init__(self, *,
                 gm: float,
                 id: Optional[str] = None):
        """
        Args:
            component_id: unique ID
            vnodes: [n1, n2] (control voltage = V(n2) - V(n1))
            gm: transconductance in Siemens (A/V)
        """
        self.gm = gm
        super().__init__(id=id)

    def __component_typename__(self) -> str:
        return "VCCS"

    def __value__(self) -> str | None:
        return str(self.gm) + "*(V(" + str(self.vnodes[1]) + ")-V(" + str(self.vnodes[0]) + "))"

    def connect(self, vnodes: Tuple[Node, Node]):
        # Connect the VCCS to its controlling voltage nodes.
        # This is separate from the main circuit connections to allow flexibility in defining the control voltage.
        # The main circuit connections (self.nodes) define where the current source injects current, while vnodes
        # define how the control voltage is measured.
        # For example, a VCCS could inject current between nodes A and B, but be controlled by the voltage
        # difference between nodes C and D.
        # This separation allows for more complex circuit configurations and is common in SPICE-like simulators.
        # The user must call this method to set the control voltage nodes after adding the VCCS to the circuit.
        # Controlling voltage is V(vnodes[1]) - V(vnodes[0]), and the current injected is gm * control_voltage.
        self.vnodes = vnodes

    def stamp(self, ctx: Context):
        gm = self.gm
        i, j = ctx.idx_query_fn(self)
        in_neg, in_pos = ctx.idx_query_fn(self.vnodes)

        if i is not None:
            if in_neg is not None:
                # Yip
                ctx.Y[i,in_neg] -= gm
            if in_pos is not None:
                # Yiq
                ctx.Y[i,in_pos] += gm
        if j is not None:
            if in_neg is not None:
                # Yjp
                ctx.Y[j,in_neg] += gm
            if in_pos is not None:
                #Yjq
                ctx.Y[j,in_pos] -= gm

    def current(self, ctx: Context) -> complex:
        in_neg, in_pos = ctx.idx_query_fn(self.vnodes)
#        _, _, in_neg, in_pos = ctx.idx_query_fn(self)
        if in_neg is None:
            v_neg = 0
        else:
            v_neg = ctx.x[in_neg]
        if in_pos is None:
            v_pos = 0
        else:
            v_pos = ctx.x[in_pos]
        return self.gm * (v_pos-v_neg)


