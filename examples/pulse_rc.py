import matplotlib.pyplot as plt
import numpy as np

from impulso import *


plt.rcParams['axes.xmargin'] = 0

V1 = PulseVoltageSource(v1=0,
                        v2=1,
                        delay=0,
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

time, voltages, currents = solve_transient(circuit,1, .01)
plt.plot(time, np.real(voltages[2]),'k')
plt.suptitle('Voltage across capacitor')
plt.title('R=50 Ohms, C=1mF, Pulse width=0.1s, Pulse amplitude=1V')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.grid()
plt.show()
