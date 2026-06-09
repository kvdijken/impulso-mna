from typing import List, Tuple, Dict, Iterable, Any

from .base import Analysis
from .circuit import Circuit
from .acdc import solve_ac, solve_dc, Statistics, StatisticsScope
from .components.component import Component, Context
from .sources.dcvoltagesource import DCVoltageSource
from .sources.dccurrentsource import DCCurrentSource




def ac_sweep(circuit: Circuit,
             freqs: List[float],
             show_output: bool = False,
             stats: Statistics = None # if not None, this function will not own the stats and not print them
            ) -> dict[float, # frequency
                      Tuple[Dict[int | str, complex], # node voltages
                            Dict[str | Component, complex]]]: # currents through components
    """
    Run AC sweep over multiple frequencies.

    Returns:
        dict freq -> (node_voltage, comp_currents)
    """
    with StatisticsScope(show_output,stats) as _stats:
        result = solve_ac(circuit,
                        freqs,
                        show_output=show_output,
                        stats=_stats)
    return result


def iter_with_last(iterable):
    it = iter(iterable)

    try:
        prev = next(it)
    except StopIteration:
        return

    for item in it:
        yield prev, False
        prev = item

    yield prev, True


def dc_sweep(circuit: Circuit,
             dc_source: DCVoltageSource | DCCurrentSource,
             dc_range: Iterable[float],
             show_output: bool = False,
             stats: Statistics = None # if not None, this function will not own the stats and not print them
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
    first = True
    with StatisticsScope(show_output,stats) as _stats:
        for dc in dc_range:
            if isinstance(dc_source, DCVoltageSource):
                dc_source.voltage = dc
            elif isinstance(dc_source, DCCurrentSource):
                dc_source.set_current(dc)
            vdc, idc = solve_dc(circuit,
                                show_output=show_output and first,
                                stats=_stats)
            first = False
            vdc_.append(vdc)
            idc_.append(idc)
    return vdc_, idc_


