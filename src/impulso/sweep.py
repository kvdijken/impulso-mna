from typing import List, Tuple, Dict, Iterable, Any


from .circuit import Circuit
from .acdc import _solve_acdc, solve_ac
from .components.component import Component
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
    return solve_ac(circuit, freqs)


def dc_sweep(circuit: Circuit,
             dc_source: DCVoltageSource | DCCurrentSource,
             dc_range: Iterable[float]
             )  -> Tuple[List[Any], # where Any is Dict[int | str, complex] (these are voltages)
                         List[Any]]: # where Any is Dict[str | Component, complex] (these are currents)
    '''
    Run DC sweep over multiple values of a voltage or current source.

    Args:
        circuit: The circuit to analyze.
        dc_source: The voltage or current source to sweep.
        dc_range: The values to sweep the source over.

    Returns:
        A tuple of two lists: (voltages, currents) where
        - the first list contains the node voltages
        - the second list the component currents
        for each value in dc_range.
    '''
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


