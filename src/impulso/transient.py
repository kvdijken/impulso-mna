import os
from collections import defaultdict
from typing import Dict, List, Tuple, Type

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
        self.ctx.dt = dt


    def node_administration(self):
        # --- Separate components by their type ---
        self.all = defaultdict(list)
        for comp in self.components:
            self.all[type(comp)].append(comp)
        super().node_administration()


    def _solve(self,
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

        # For inductors set initial current at t=0
        initial_currents = {}
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

        # For capacitors set initial voltage across terminals at t=0
        initial_voltages = {}
        for cap in self.all.get(Capacitor, []):
            n1, n2 = self.nodes[cap]
            v_initial = cap.initial_voltage # v_initial = v2 - v1
            if n2 != self.ground_node:
                voltage[n2] = voltage.get(n1) + v_initial # there has already been a solve_mna call,
                                                          # so voltage[n1] should be set to the correct
                                                          # value for n1 at t=0
                # Check for conflicts with the voltage at n2 that may have already been set by
                # another capacitor. This should not happen because we expect the user to
                # only set the initial voltage for each node once, but we check for this
                # just in case to avoid silent errors.
                assert initial_voltages.get(n2, voltage[n2]) == voltage[n2], f"Conflicting initial voltages for node {n2}."
                initial_voltages[n2] = voltage[n2]
            else:
                # n2 is ground
                voltage[n1] = -v_initial
                # Check for conflicts with the voltage at n1 that may have already been set by
                # another capacitor. This should not happen because we expect the user to
                # only set the initial voltage for each node once, but we check for this
                # just in case to avoid silent errors.
                assert initial_voltages.get(n1, -v_initial) == -v_initial, f"Conflicting initial voltages for node {n1}."
                initial_voltages[n1] = -v_initial

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


    def solve(self,
              t_stop: float,
              dt: float
              ) -> Tuple[np.ndarray, List[Dict[int, float]], List[Dict[str | Component, float]]]:
        '''              ^time       ^node voltages          ^component currents
        '''
        self.ctx.analysis_type = Analysis.IC
        self.node_administration()

        # Create time series
        times = np.arange(0, t_stop + dt / 2, dt)

        for comp in self.components:
            comp.init_state()

        C1 = self.circuit['C1']
        print("Cap state:", C1.previous_voltage)

        # Get the initial voltages for the other nodes
        self.ctx.t = times[0]
        voltage, current = self.solve_mna(return_real=True)
        for comp in self.components:
            comp.update_state(self.ctx)

        print("Node4:", voltage[4])
        n1, n2 = self.circuit.nodes[C1]
        v1 = 0 if n1 == 0 else voltage[n1]
        v2 = 0 if n2 == 0 else voltage[n2]

        print("Cap voltage after first solve:", v2 - v1)

        # Prepare history with the initial voltages for all nodes
        # now at t=0
        self.ctx.voltage_history = [voltage.copy()]
        self.ctx.current_history = [current.copy()]

        try:
            self.ctx.analysis_type = Analysis.TRANSIENT
            self.node_administration()

            for t in times:
                self.ctx.t = t
                if os.environ.get("IMPULSO_DEBUG", '0') == '1':
                    print(f"Time: {t} s\n")
                voltage, current = self.solve_mna(return_real=True)
                self.ctx.voltage_history.append(voltage.copy())
                self.ctx.current_history.append(current.copy())
                for comp in self.components:
                    comp.update_state(self.ctx)
        except np.linalg.LinAlgError as e:
            print(f"Linear algebra error at time {self.ctx.t}: {e}")
            times = times[:len(self.ctx.voltage_history)-1]

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


