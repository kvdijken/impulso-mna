# Ebers-Moll approximation as in https://en.wikipedia.org/wiki/Bipolar_junction_transistor

import uuid
from typing import Dict, List, Tuple, Optional, Type, Protocol

from ..base import Analysis
from .diode import Diode
from .capacitor import Capacitor
from ..sources.cccs import CCCS
from .component import Component, CompoundComponent, Context
from ..sources.dcvoltagesource import DCVoltageSource


class NPNLike(Protocol):
    Va: float # Early voltage

    # internal nodes
    _b0: str # internal node between base and base-emitter diode
    _e0: str # internal node between emitter and base-emitter diode
    _c0: str # internal node between collector and base-collector diode


class Rout(Component):
    ''' Output resistance, which is a CCR. '''

    def __init__(self,
                 npn: NPNLike,
                 ):
        self.npn = npn
        super().__init__(id=f"{npn.id}_Rout")

    def augments(self):
        return False

    def admittance(self, s: Optional[complex] = None) -> complex:
        assert False, "Rout is a non-linear component and does not have a fixed admittance. Use the stamp method to account for its non-linearity."

    def linear(self):
        return False

    def stamp(self, ctx: Context):
        ac_analysis = ctx.analysis_type == Analysis.AC
        if ac_analysis:
            g = self.admittance_ac
        else:
            # collector current
            ic = -self.npn.v0c.current(ctx)

            # calculate rout
            g = max(ic, 1e-12) / self.npn.Va

        # stamp
        i, j = ctx.idx_query_fn(self)
        assert i is not None # internal node, never ground
        assert j is not None # internal node, never ground
        ctx.Y[i, i] += g
        ctx.Y[j, j] += g
        ctx.Y[i, j] -= g
        ctx.Y[j, i] -= g

    def set_admittance_for_ac(self, i_dc: float):
        self.admittance_ac = i_dc / self.npn.Va

    def current(self, ctx: Context) -> complex:
        i, j = ctx.idx_query_fn(self)
        if i is None:
            vi = 0
        else:
            vi = ctx.x[i]
        if j is None:
            vj = 0
        else:
            vj = ctx.x[j]
        vd = (vi - vj) # voltage over Rout
        ic = -self.npn.v0c.current(ctx) # collector current
        g = max(ic, 1e-12) / self.npn.Va
        return vd * g

class BJT(CompoundComponent):
    # Ebers-Moll approximation for a BJT

    # Should be connected as [emitter, base, collector]
    # external nodes
    __emitter = 0
    __base = 1
    __collector = 2

    # internal nodes
    _b0: str # internal node between base and base-emitter diode
    _e0: str # internal node between emitter and base-emitter diode
    _c0: str # internal node between collector and base-collector diode

    # Early voltage
    Va: float


    def __init__(self,
                 bjttype: str,
                 alpha_f: float,
                 alpha_r: float,
                 ro: float,
                 Va: float,
                 cbc: float,
                 cbe: float,
                 id=None,
                 ):
        assert(bjttype in ['NPN', 'PNP']), f"Invalid BJT type {type}. Must be 'NPN' or 'PNP'."
        self.bjttype = bjttype
        self.alpha_f = alpha_f
        self.alpha_r = alpha_r
        self.ro = ro
        self.Va = Va
        super().__init__(id=id)
        self._id = uuid.uuid4().hex
        self._b0 = f"{self.id}_b0"
        self._e0 = f"{self.id}_e0"
        self._e02 = f"{self.id}_e02"
        self._c0 = f"{self.id}_c0"
        self._c02 = f"{self.id}_c02"
        self.cbc = cbc
        self.cbe = cbe

    def before_add(self,
                   circuit: 'Circuit',
                   nodes: List[int]
                   ) -> Tuple[bool, bool]:
        #                     ^add  ^current
        e = nodes[self.__emitter]
        b = nodes[self.__base]
        c = nodes[self.__collector]

        # All terminal zero volt voltage source point outwards to measure currents

        # internal zero volt voltage source to measure base current
        self.v0b = DCVoltageSource(0, id=f"{self.id}_V0b")
        circuit.add(self.v0b, [self._b0,b])

        # internal zero volt voltage source to measure emitter current
        self.v0e = DCVoltageSource(0, id=f"{self.id}_V0e")
        circuit.add(self.v0e, [self._e0,e])

        # internal zero volt voltage source to measure base-emitter diode current
        self.v0e2 = DCVoltageSource(0, id=f"{self.id}_V0e2")
        circuit.add(self.v0e2, [self._e02,self._e0])

        # base-emitter diode
        self.be_diode = Diode(id=f"{self.id}_Dbe")
        if self.bjttype == 'NPN':
            circuit.add(self.be_diode, [self._b0,self._e02])
        else:
            circuit.add(self.be_diode, [self._e02,self._b0])

        # base-collector diode
        self.bc_diode = Diode(id=f"{self.id}_Dbc")
        if self.bjttype == 'NPN':
            circuit.add(self.bc_diode, [self._b0,self._c02])
        else:
            circuit.add(self.bc_diode, [self._c02,self._b0])

        # internal zero volt voltage source to measure base-collector diode current
        self.v0c2 = DCVoltageSource(0, id=f"{self.id}_V0c2")
        circuit.add(self.v0c2, [self._c02,self._c0])

        # internal zero volt voltage source to measure collector current
        self.v0c = DCVoltageSource(0, id=f"{self.id}_V0c")
        circuit.add(self.v0c, [self._c0,c])

        # forward current amplification
        if self.bjttype == 'NPN':
            _a = self.alpha_f
        else:
            _a = -self.alpha_f
        self.cccs_f = CCCS(A=_a, id=f"{self.id}_CCCSf")
        if self.bjttype == 'NPN':
            circuit.add(self.cccs_f, [self._c0,self._b0])
        else:
            circuit.add(self.cccs_f, [self._b0,self._c0])
        self.cccs_f.connect(self.v0e2)

        # reverse current amplification
        if self.bjttype == 'NPN':
            _a = self.alpha_r
        else:
            _a = -self.alpha_r
        self.cccs_r = CCCS(A=_a, id=f"{self.id}_CCCSr")
        if self.bjttype == 'NPN':
            circuit.add(self.cccs_r, [self._e0,self._b0])
        else:
            circuit.add(self.cccs_r, [self._b0,self._e0])
        self.cccs_r.connect(self.v0c2)

        # output resistance
        self.rout = Rout(self)
        circuit.add(self.rout, [self._e0,self._c0])

        # base-collector capacitance
        self.cbc_cap = Capacitor(self.cbc, id=f"{self.id}_Cbc")
        circuit.add(self.cbc_cap, [self._b0,self._c0])

        # base emitter capacitance
        self.cbe_cap = Capacitor(self.cbe, id=f"{self.id}_Cbe")
        circuit.add(self.cbe_cap, [self._b0,self._e0])

        return False, True
        # False: do not add this BJT itself
        # True: does deliver current info

    def admittance(self, s: Optional[complex] = None) -> complex:
        # Should never be called
        assert False, "NPN is a non-linear component and does not have a fixed admittance. Use the stamp method to account for its non-linearity."

    def augments(self) -> None:
        return False

    def current(self, ctx: Context) -> Tuple[complex,complex,complex]:
        # All currents positive going out of the terminal
        ie = self.v0e.current(ctx)
        ib = self.v0b.current(ctx)
        ic = self.v0c.current(ctx)
        return (ie, ib, ic)

    def stamp(self, ctx: Context):
        pass


class NPN(BJT):
    ''' NPN transistor modeled using the Ebers-Moll approximation.'''

    def __init__(self,
                 alpha_f=0.997,
                 alpha_r=1e-3,
                 ro=1e4,
                 Va=50,
                 cbc=4e-12,
                 cbe=12e-12,
                 id=None):

        super().__init__(bjttype='NPN',
                         id=id,
                         alpha_f=alpha_f,
                         alpha_r=alpha_r,
                         ro=ro,
                         cbc=cbc,
                         cbe=cbe,
                         Va=Va)


class PNP(BJT):
    ''' PNP transistor modeled using the Ebers-Moll approximation.'''

    def __init__(self,
                 alpha_f=0.997,
                 alpha_r=1e-3,
                 ro=1e4,
                 Va=50,
                 cbc=4e-12,
                 cbe=10e-12,
                 id=None):

        super().__init__(bjttype='PNP',
                         id=id,
                         alpha_f=alpha_f,
                         alpha_r=alpha_r,
                         ro=ro,
                         cbc=cbc,
                         cbe=cbe,
                         Va=Va)


# Utility functions to retrive emitter, base and collector currents from .a list of currents returned by BJT.current()
def emitter_current(i: list[Tuple[complex,complex,complex]]) -> list[complex]:
    return [i[0] for i in i]

def base_current(i: list[Tuple[complex,complex,complex]]) -> list[complex]:
    return [i[1] for i in i]

def collector_current(i: list[Tuple[complex,complex,complex]]) -> list[complex]:
    return [i[2] for i in i]

