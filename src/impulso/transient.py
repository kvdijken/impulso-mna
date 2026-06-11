import os
from collections import defaultdict
from typing import Dict, List, Tuple, Type
import time
import sys

import numpy as np

from .components.component import *
from .sources.source import *
from .acdc import Solver_ACDC, Statistics, Statistics
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
                f"({int(pct)}%)"
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
            self._active = False



class Solver_Transient(Solver_ACDC):

    all: Dict[Type[Component], List[Component]] = {} # sorted catalog of components by type

    def __init__(self,
                 circuit: Circuit,
                 dt: float):
        # augment context for transient analysis
        self.dt = dt
        super().__init__(circuit)


    def _create_context(self, freq: float | None) -> Context:
        ctx = super()._create_context(freq)
        ctx.dt = self.dt
        ctx.analysis_type = Analysis.TRANSIENT
        return ctx


    def _node_administration(self):
        # --- Separate components by their type ---
        self.all = defaultdict(list)
        for comp in self.components:
            self.all[type(comp)].append(comp)
        super()._node_administration()


    def __estimate_solution(self):
        # TODO This is not safe, layout of ctx.x may have changed
        if True and hasattr(self.ctx, 'x') and (self.ctx.x is not None) and (len(self.ctx.x) == self.N):
            return np.copy(self.ctx.x)
        else:
            return np.zeros(self.N, dtype=complex)


    def solve(self,
              t_stop: float,
              dt: float,
              show_output: bool = False,
              stats: Statistics = None # if not None, this function will not own the stats and not print them
              ) -> Tuple[np.ndarray, List[Dict[int, float]], List[Dict[str | Component, float]]]:
        '''              ^time       ^node voltages          ^component currents
        '''
        self._show_output = show_output
        with Statistics(show_output,stats) as self._stats:
            self.ctx = self._create_context(freq=None) # create context with transient analysis type
            # Create time series
            times = np.arange(0, t_stop + dt / 2, dt)

            # Initial conditions
            self.ctx.analysis_type = Analysis.IC
            if show_output:
                print("\nSolving for initial conditions:")
            self._node_administration()
            for comp in self.components:
                comp.init_state()
            self.ctx.t = times[0]
            voltage, current = self._solve_mna(return_real=True)

            if show_output:
                print("\nTransferring state from initial conditions.")
            # Transfer state from Initicial Conditions solve to the components,
            # so that they can use this state during the transient solve
            for comp in self.components:
                comp.initialize_transient_state(self.ctx)

            self._initialize()
            if show_output:
                print("\nStarting transient solve:")
            self.ctx.analysis_type = Analysis.TRANSIENT
            self._node_administration()
            self.ctx.t = times[0]
            self.ctx.dt = dt

            # Prepare history with the initial voltages for all nodes
            # now at t=0
            self.ctx.voltage_history = [voltage.copy()]
            self.ctx.current_history = [current.copy()]

            self._reset_cache() # clear cache after initial conditions have been set and solved for,
                                # so that we don't accidentally use cached values from the IC solve
                                # during the transient solve

            with ProgressReporter(self.ctx, total=t_stop) as progress:
                try:
                    for t in times[1:]:
                        self.ctx.t = t
                        voltage, current = self._solve_mna(return_real=True)
                        if show_output:
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
                    if show_output:
                        print(f"Linear algebra error at time {self.ctx.t}: {e}")
                    times = times[:len(self.ctx.voltage_history)]
        return times, self.ctx.voltage_history, self.ctx.current_history




def solve_transient(circuit: Circuit,
                    t_stop: float,
                    dt: float,
                    show_output: bool = False,
                    stats: Statistics = None
                    ) -> Tuple[np.ndarray,          # time
                               Dict[int,            # node
                                    List[float]],   # voltage over time
                               Dict[str|Component, # component
                                    List[float]     # current over time
                               ]]:
    solver = Solver_Transient(circuit, dt=dt)
    with Statistics(show_output,stats) as _stats:
        time, _v, _c = solver.solve(t_stop, dt, show_output=show_output, stats=_stats)
        _v = transpose_dicts(_v)
        _c = transpose_dicts(_c)
    return time, _v, _c


