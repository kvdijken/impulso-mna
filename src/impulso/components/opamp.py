from typing import Optional

from .component import Component, Context


LARGE_CONDUCTANCE = 1e12


class Opamp(Component):
    ''' Connect as [pos, neg, out] '''

    __pos: int = 0
    __neg: int = 1
    __out: int = 2

    """Ideal op-amp with infinite gain, zero input current, and zero output impedance."""

    A = 1e6  # large gain to approximate ideal behavior

    def __init__(self, id: Optional[str] = None):
        super().__init__(id)

    def admittance(self, s: Optional[complex] = None) -> complex:
        return LARGE_CONDUCTANCE  # ideal op-amp has zero output impedance, so infinite admittance

    def gain(self) -> float:
        return self.A

    def augments(self):
        return True

    def stamp(self, ctx: Context):
        nodes = ctx.idx_query_fn(self)
        augm = ctx.augm_query_fn(self)
        pos = nodes[Opamp.__pos]
        neg = nodes[Opamp.__neg]
        out = nodes[Opamp.__out]

        # Vout = A*(Vpos - Vneg)
        if pos is not None:
            ctx.Y[augm,pos] += self.gain()
        if neg is not None:
            ctx.Y[augm,neg] -= self.gain()
        ctx.Y[augm,out] -= 1

        # output current
        ctx.Y[out,augm] -= 1

    def current(self, ctx: Context) -> complex:
        augm = ctx.augm_query_fn(self)
        return ctx.x[augm]
