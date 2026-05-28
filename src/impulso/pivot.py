from typing import List, Tuple, Dict, Union, TypeVar
from collections import defaultdict
from bisect import bisect_left, bisect_right
from typing import Dict, Hashable, Literal, Tuple, TypeVar



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



K = TypeVar('K', bound=Hashable)

NodeType = Union[int, str]
ComponentType = Union[str, "Component"]

def _pivot_generic(data: List[Dict[K, complex]]) -> Dict[K, List[complex]]:
    """Generic helper to pivot a sequence of mappings into a mapping of keys to lists.

    Parameters
    ----------
    data:
        List of dictionaries mapping keys (hashable) to complex values.

    Returns
    -------
    Dict[Hashable, List[complex]]
        Mapping from each key found to the list of values encountered in order.
    """
    out: Dict[K, List[complex]] = defaultdict(list)
    for d in data:
        for k, v in d.items():
            out[k].append(v)
    return dict(out)


def v_pivot(data: list[Dict[NodeType, complex]] # list[node -> voltage at that node]
            )-> Dict[NodeType, List[complex]]: # node -> list of voltages
    """Pivot node-voltage history data into per-node voltage traces.

    Parameters
    ----------
    data:
        Sequence of mappings from node identifiers to complex node voltages.
        Node identifiers may be either integers or strings.

    Returns
    -------
    Dict[NodeType, List[complex]]
        Mapping from each node identifier to the list of voltages seen in order.
    """
    return _pivot_generic(data)  # type: ignore[return-value]


def i_pivot(data: list[Dict[ComponentType, complex]] # list[component -> component current]
            )-> Dict[ComponentType, List[complex]]: # component -> list of currents
    """Pivot component-current history data into per-component current traces.

    Parameters
    ----------
    data:
        Sequence of mappings from component identifiers to complex component currents.
        Component identifiers may be component `id` strings or `Component` objects.

    Returns
    -------
    Dict[ComponentType, List[complex]]
        Mapping from each component identifier to the list of currents seen in order.
    """
    return _pivot_generic(data)  # type: ignore[return-value]


def transpose_dicts(data:List[Dict[K,float]]) -> Dict[K,List[float]]:
    '''
    Transpose a list of key–value mappings into
    a mapping of keys to value sequences.
    '''
    result = defaultdict(list)
    for d in data:
        for k, v in d.items():
            result[k].append(v)
    return dict(result)


def time_slice(
    *,
    time: list[float],                 # time, ascending order
    data: Dict[K, list[float]],        # data series
    start: float,                      # start of time slice
    end: float,                        # end of time slice
    inclusive: bool = True,            # include start/end if equal
    returns: Literal['data', 'indices'] = 'data'
) -> (
    Tuple[list[float], Dict[K, list[float]]]
    | Tuple[int, int]
):
    """
    Slice time-series data between `start` and `end`.

    Parameters
    ----------
    time:
        Ascending list of time values.
    data:
        Dictionary mapping keys to data vectors of equal length as `time`.
    start:
        Start time of slice.
    end:
        End time of slice.
    inclusive:
        If True:
            include samples where time == start or time == end.
        If False:
            exclude samples where time == start or time == end.
    returns:
        'data':
            return sliced time and data.
        'indices':
            return slice indices (i0, i1), usable as [i0:i1].

    Returns
    -------
    If returns == 'data':
        (
            sliced_time,
            sliced_data
        )

    If returns == 'indices':
        (
            start_index,
            end_index
        )

    Notes
    -----
    The returned end index is exclusive, matching Python slicing semantics.
    """

    if start > end:
        raise ValueError("start must be <= end")

    if inclusive:
        i0 = bisect_left(time, start)
        i1 = bisect_right(time, end)
    else:
        i0 = bisect_right(time, start)
        i1 = bisect_left(time, end)

    if returns == 'indices':
        return i0, i1

    if returns != 'data':
        raise ValueError("returns must be 'data' or 'indices'")

    sliced_time = time[i0:i1]
    sliced_data = {
        key: values[i0:i1]
        for key, values in data.items()
    }

    return sliced_time, sliced_data


def realify(data: Dict[K, List[complex]] | List[complex]) -> Dict[K, List[float]] | List[float]:
    """Convert complex values to their real parts.

    Parameters
    ----------
    data:
        Either a mapping from keys to lists of complex values, or a simple list of complex values.

    Returns
    -------
    Dict[K, List[float]] | List[float]
        If given a dict, returns a dict with the same keys and lists of real parts.
        If given a list, returns a list of real parts.
    """
    if isinstance(data, dict):
        return {k: [v.real for v in lst] for k, lst in data.items()}
    return [v.real for v in data]


def imagify(data: Dict[K, List[complex]] | List[complex]) -> Dict[K, List[float]] | List[float]:
    """Convert complex values to their imaginary parts.

    Parameters
    ----------
    data:
        Either a mapping from keys to lists of complex values, or a simple list of complex values.

    Returns
    -------
    Dict[K, List[float]] | List[float]
        If given a dict, returns a dict with the same keys and lists of imaginary parts.
        If given a list, returns a list of imaginary parts.
    """
    if isinstance(data, dict):
        return {k: [v.imag for v in lst] for k, lst in data.items()}
    return [v.imag for v in data]


def magify(data: Dict[K, List[complex]] | List[complex]) -> Dict[K, List[float]] | List[float]:
    """Convert complex values to their magnitudes.

    Parameters
    ----------
    data:
        Either a mapping from keys to lists of complex values, or a simple list of complex values.

    Returns
    -------
    Dict[K, List[float]] | List[float]
        If given a dict, returns a dict with the same keys and lists of magnitudes.
        If given a list, returns a list of magnitudes.
    """
    if isinstance(data, dict):
        return {k: [abs(v) for v in lst] for k, lst in data.items()}
    return list(map(np.abs, data))

