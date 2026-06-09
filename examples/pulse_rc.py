# This script simulates a simple RC circuit driven by a single pulse voltage source and plots the capacitor voltage over time.
#
# - It creates a pulse source `V1` that switches from 0 V to 1 V for 0.1 s, starting at 0.25 s, with a total period of 1 s.
# - It connects that source to a 50 Ω resistor `R1` and a 1 mF capacitor `C1`.
# - The capacitor is initialized with an initial voltage of -0.5 V.
# - The circuit is solved with a transient analysis from 0 to 1 s using 0.01 s time steps.
# - Finally, it plots the voltage at the capacitor node over time.

import matplotlib.pyplot as plt
import numpy as np

from impulso import *


plt.rcParams['axes.xmargin'] = 0

V1 = PulseVoltageSource(v1=0,
                        v2=1,
                        delay=0.25,
                        rise_time=0,
                        fall_time=0,
                        pulse_width=0.1,
                        period=1,
                        n_periods=1,
                        id='V1')
R1 = Resistor(resistance=50, id='R1')
C1 = Capacitor(capacitance=1e-3,id='C1',initial_voltage=-0.5)

circuit = Circuit()
circuit.add(V1,[0,1])
circuit.add(R1,[1,2])
circuit.add(C1,[2,0])

time, voltages, currents = solve_transient(circuit,1, .01, show_output=True)
plt.plot(time, np.real(voltages[2]),'k')
plt.suptitle('Voltage across capacitor')
plt.title('R=50 Ohms, C=1mF, Pulse width=0.1s, Pulse amplitude=1V')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.grid()
plt.show()
