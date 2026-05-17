from typing import List, Tuple, Dict, Union
from collections import defaultdict

import numpy as np

from .components.component import Component


def freq_pivot_and_select(data: dict[float, # frequency
                                Tuple[Dict[int | str, complex], # node voltages
                                      Dict[str | Component, complex]]], # component currents
                     voltage_nodes: List[int | str] = None, # which node voltages to return
                     current_components: List[str | Component] = None, # which component currents to return
                     to_return: str = 'M', # whether to return magnitude, phase, magnitude+phase, real, imaginary, or complex
                     deg: bool = True,
                     unwrap_phase: bool = True
          ) -> Tuple[list[float], # frequencies
                     Dict[int | str, List[complex]], # node voltages over frequencies
                     Dict[str | Component, List[complex]] # component currents over frequencies
                    ]:
    '''
    Pivot the results of an AC sweep and select the desired node voltages and component currents.
    Args:
        data: dict freq -> (node_voltage, comp_currents)
        node_voltages: which node voltages to return. If None, return all. If [], return none.
        component_currents: which component currents to return. If None, return all. If [], return none.
        to_return: whether to return magnitude, phase, magnitude+phase, real, imaginary, or complex
                'M': magnitude
                'P': phase
                'MP': magnitude and phase as a tuple
                'R': real part
                'I': imaginary part
                'C': complex number
    Returns:
        freqs: list of frequencies
        node_voltages: dict node -> list of voltages over frequencies
        component_currents: dict component -> list of currents over frequencies
    '''

    def output(c: complex):
        match to_return:
            case 'M':
                return np.abs(c)
            case 'P':
                return np.angle(c, deg=deg)
            case 'MP':
                return (np.abs(c), np.angle(c, deg=deg))
            case 'R':
                return np.real(c)
            case 'I':
                return np.imag(c)
            case 'C':
                return c

    def unwrap(arr):
        if to_return == 'P':
            return np.unwrap(arr, period=360 if deg else 2*np.pi)
        elif to_return == 'MP':
            mag = arr[0]
            phase = arr[1]
            return np.array(mag), np.unwrap(phase, period=360 if deg else 2*np.pi)
        else:
            return arr

    assert to_return in ['M', 'P', 'MP', 'R', 'I', 'C'], "to_return must be one of 'M', 'P', 'MP', 'R', 'I', or 'C'"
    freqs = list(data.keys())
    first_voltages, first_currents = next(iter(data.values()))

    # Determine which node voltages to return
    if voltage_nodes is None:
        voltage_nodes = first_voltages.keys()
    else:
        assert set(voltage_nodes) - set(first_voltages.keys()) == set(), "Some specified voltage nodes are not present in the data"
        voltage_nodes = set(voltage_nodes) & set(first_voltages.keys())
    voltages = {
        node: unwrap(np.array(output([data[f][0][node] for f in freqs]))) for node in voltage_nodes
    }

    # Determine which component currents to return
    if current_components is None:
        current_components = first_currents.keys()
    else:
        assert set(current_components) - set(first_currents.keys()) == set(), "Some specified current components are not present in the data"
        current_components = set(current_components) & set(first_currents.keys())
    currents = {
        comp: output(np.array([data[f][1][comp] for f in freqs]))
               for comp in current_components
    }

    return freqs, voltages, currents



NodeType = Union[int, str]
ComponentType = Union[str, "Component"]

def v_pivot(data: list[Dict[NodeType, complex]] # list[node -> voltage at that node]
            )-> Dict[NodeType, List[complex]]: # node -> list of voltages

    out: Dict[NodeType, List[complex]] = defaultdict(list)
    for d in data:
        for k, v in d.items():
            out[k].append(v)
    return dict(out)


def i_pivot(data: list[Dict[ComponentType, complex]] # list[component -> component current]
            )-> Dict[ComponentType, List[complex]]: # component -> list of currents

    out: Dict[ComponentType, List[complex]] = defaultdict(list)
    for d in data:
        for k, v in d.items():
            out[k].append(v)
    return dict(out)

