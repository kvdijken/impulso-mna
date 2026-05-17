import os
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Type

import numpy as np

from .components.component import *
from .sources.source import *
from .acdc import Solver_ACDC
from .components.capacitor import Capacitor
from .components.inductor import Inductor
from .circuit import Circuit
from .pivot import transpose_dicts


class Solver_Transient(Solver_ACDC):

    all: Dict[Type[Component], List[Component]] = {} # sorted catalog of components by type

    def __init__(self,
                 circuit: Circuit,
                 dt: float):
        super().__init__(circuit)

        # augment context for transient analysis
        self.ctx.analysis_type = Analysis.TRANSIENT
        self.ctx.dt = dt


    def node_administration(self):
        # --- Separate components by their type ---
        self.all = defaultdict(list)
        for comp in self.components:
            self.all[type(comp)].append(comp)
        super().node_administration()


    def solve(self,
              t_stop: float,
              dt: float
              ) -> Tuple[np.ndarray, List[Dict[int, float]], List[Dict[str | Component, float]]]:
        '''              ^time       ^node voltages          ^component currents
        '''
        self.node_administration()

        # Create time series
        times = np.arange(0, t_stop + dt / 2, dt)

        voltage = {n: 0.0 for n in self.all_nodes()}
        current = {comp.id: 0.0 for comp in self.components}

        initial_voltages = {}
        initial_currents = {}

        # For capacitors set initial voltage across terminals at t=0
        for cap in self.all.get(Capacitor, []):
            n1, n2 = self.nodes[cap]
            v_initial = cap.initial_voltage # v_initial = v2 - v1
            if n2 != self.ground_node:
                voltage[n2] = voltage.get(n1, 0.0) + v_initial
                initial_voltages[n2] = voltage[n2]
            else:
                # n2 is ground
                voltage[n1] = -v_initial
                initial_voltages[n1] = -v_initial

        # For inductors set initial current at t=0
        for ind in self.all.get(Inductor, []):
            i_initial = ind.initial_current
            current[ind] = i_initial
            initial_currents[ind] = i_initial

        # Prepare history
        self.ctx.voltage_history = [voltage.copy()]
        self.ctx.current_history = [current.copy()]

        # Get the initial voltages for the other nodes
        self.ctx.t = times[0]
        voltage, current = self.solve_mna(return_real=True)
        # Overwrite the voltage history at t=0 with the initial
        # voltages for the capacitor nodes
        for n in initial_voltages.keys():
            voltage[n] = initial_voltages[n]

        # Overwrite the current history at t=0 with the initial
        # currents for the inductor components
        for ind in initial_currents.keys():
            current[ind] = initial_currents[ind]

        # Prepare history with the initial voltages for all nodes
        # now at t=0
        self.ctx.voltage_history = [voltage.copy()]
        self.ctx.current_history = [current.copy()]

        for t in times:
            self.ctx.t = t
            if os.environ.get("IMPULSO_DEBUG", '0') == '1':
                print(f"Time: {t} s\n")
            voltage, current = self.solve_mna(return_real=True)
            self.ctx.voltage_history.append(voltage.copy())
            self.ctx.current_history.append(current.copy())

        # TODO: check capacitor current
        # TODO: describe why we do not return entire history (we return history[:-1] because the last entry is after the last time step)
        return times, self.ctx.voltage_history[:-1], self.ctx.current_history[:-1]


def solve_transient(circuit: Circuit,
                    t_stop: float,
                    dt: float,
                    ) -> Tuple[np.ndarray,          # time
                               Dict[int,            # node
                                    List[float]],   # voltage over time
                               Dict[str|Component, # component
                                    List[float]     # current over time
                               ]]:
    solver = Solver_Transient(circuit,
                              dt=dt)
    time, _v, _c = solver.solve(t_stop, dt)
    _v = transpose_dicts(_v)
    _c = transpose_dicts(_c)
    return time, _v, _c


