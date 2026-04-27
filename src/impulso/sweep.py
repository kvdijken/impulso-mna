from typing import List, Tuple, Dict, Union, Iterable
from collections import defaultdict

import numpy as np

from .base import Analysis
from .circuit import Circuit
from .acdc import _solve_acdc
from .components.component import Component, Context
from .sources.dcvoltagesource import DCVoltageSource
from .sources.dccurrentsource import DCCurrentSource




def ac_sweep(circuit: Circuit, 
             freqs: List[float]
            ) -> dict[float, # frequency
                      Tuple[Dict[int | str, complex], # node voltages
                            Dict[str | Component, complex]]]: # currents through components
    """
    Run AC sweep over multiple frequencies.

    Returns:
        dict freq -> (node_voltage, comp_currents)
    """
    non_linears = set() # all nonlinear components in the circuit
    for comp in circuit.component.values():
        if not comp.linear():
            non_linears.add(comp)

    if len(non_linears) > 0:
        # First do a operating point analysis
        vdc, idc = _solve_acdc(circuit, 0)
        for comp in non_linears:
            comp.set_admittance_for_ac(idc[comp])                    

    results = {}
    ctx = Context()
    ctx.analysis_type = Analysis.AC
    for f in freqs:
        results[f] = _solve_acdc(circuit,f,ctx=ctx)
        
    return results


def dc_sweep(circuit: Circuit, 
             dc_source: DCVoltageSource | DCCurrentSource,
             dc_range: Iterable[float]
             )  -> Tuple[List[complex], List[complex]]:
    
    dc_ = []
    vdc_ = []
    idc_ = []
    for dc in dc_range:
        if isinstance(dc_source, DCVoltageSource):
            dc_source.voltage = dc
        elif isinstance(dc_source, DCCurrentSource):
            dc_source.set_current(dc)
        vdc, idc = _solve_acdc(circuit, 0)
        vdc_.append(vdc)
        idc_.append(idc)
            
    return vdc_, idc_


