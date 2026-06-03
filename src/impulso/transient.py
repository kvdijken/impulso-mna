import os
from collections import defaultdict
from typing import Dict, List, Tuple, Type
import time
import sys

import numpy as np

from .components.component import *
from .sources.source import *
from .acdc import Solver_ACDC
from .components.capacitor import Capacitor
from .components.inductor import Inductor
from .circuit import Circuit
from .pivot import transpose_dicts


import sys
import time

import sys
import time

class ProgressReporter:
    def __init__(self, ctx, total: float | None = None, delay: float = 0):
        self.ctx = ctx
        self.total = total  # e.g. t_stop for transient, None for DC/AC
        self.delay = delay

        self._t0 = time.perf_counter()
        self._active = False
        self._last_len1 = 0
        self._last_len2 = 0

        # register into context (plug-and-play access)
        self.ctx.progress = self

    # ---------------- context manager ----------------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.finish()
        self.ctx.progress = None
        return False  # don't suppress exceptions

    # ---------------- core update ----------------
    def update(self, t: float | None = None, label: str = ""):
        now = time.perf_counter()
        elapsed_wall = now - self._t0

        if elapsed_wall < self.delay:
            return

        # mode: time-based (transient) or iteration-based (DC/AC)
        if self.total is not None and t is not None:
            pct = 100.0 * t / self.total if self.total else 100.0
            sim_speed = t / elapsed_wall if elapsed_wall > 0 else 0.0

            line1 = (
                f"Simulation: {t:12.4e}s / "
                f"{self.total:12.4e}s "
                f"({pct:6.2f}%)"
            )

            line2 = (
                f"Speed: {sim_speed:.2e} sim_s/s"
            )

        else:
            # generic mode (DC / AC iterations)
            line1 = f"Simulation: {label}"
            line2 = f"Elapsed: {elapsed_wall:.2f}s"

        self._render(line1, line2)

    # ---------------- rendering ----------------
    def _render(self, line1: str, line2: str):
        if not self._active:
            print(line1)
            print(line2)
            self._active = True
        else:
            sys.stdout.write("\x1b[2F")
            sys.stdout.write(line1.ljust(self._last_len1) + "\n")
            sys.stdout.write(line2.ljust(self._last_len2) + "\n")
            sys.stdout.flush()

        self._last_len1 = len(line1)
        self._last_len2 = len(line2)

    # ---------------- finish ----------------
    def finish(self):
        if self._active:
            print()
            self._active = False



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
        # Create time series
        times = np.arange(0, t_stop + dt / 2, dt)

        # Initial conditions
        self.ctx.analysis_type = Analysis.IC
        self.node_administration()
        for comp in self.components:
            comp.init_state()
        self.ctx.t = times[0]
        voltage, current = self.solve_mna(return_real=True)

        # Transfer state from Initicial Conditions solve to the components,
        # so that they can use this state during the transient solve
        for comp in self.components:
            comp.update_state(self.ctx)

        # Prepare history with the initial voltages for all nodes
        # now at t=0
        self.ctx.voltage_history = [voltage.copy()]
        self.ctx.current_history = [current.copy()]

        self._reset_cache() # clear cache after initial conditions have been set and solved for,
                            # so that we don't accidentally use cached values from the IC solve
                            # during the transient solve

        with ProgressReporter(self.ctx, total=t_stop) as progress:
            try:
                self.ctx.analysis_type = Analysis.TRANSIENT
                self.node_administration()
                for t in times[1:]:
                    self.ctx.t = t
                    voltage, current = self.solve_mna(return_real=True)
                    progress.update(t)
                    if os.environ.get("IMPULSO_DEBUG", '0') == '1':
                        print(f"Time: {t} s\n")
                    self.ctx.voltage_history.append(voltage.copy())
                    self.ctx.current_history.append(current.copy())
                    for comp in self.components:
                        comp.update_state(self.ctx)
            except np.linalg.LinAlgError as e:
                # Catch linear algebra errors that may occur during
                # the solve_mna calls, which may be due to numerical
                # issues or due to the circuit becoming unsolvable at
                # some point during the transient simulation. In this
                # case, we print an error message and return the
                # results up until the point where the error occurred.
                print(f"Linear algebra error at time {self.ctx.t}: {e}")
                times = times[:len(self.ctx.voltage_history)]
        return times, self.ctx.voltage_history, self.ctx.current_history


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


