import matplotlib.pyplot as plt
import numpy as np

from impulso import *


plt.rcParams['axes.xmargin'] = 0

V1 = PulseVoltageSource(v1=0, v2=1, delay=4.5, rise_time=0.2, fall_time=0.2, pulse_width=0.5, period=1, id='V1')
R1 = Resistor(resistance=50, id='R1')
C1 = Capacitor(capacitance=1e-3, id='C1', initial_voltage=-0.5)

circuit = Circuit()
circuit.add(V1,[0,1])
circuit.add(R1,[1,2])
circuit.add(C1,[2,0])

print(circuit)

time, voltages, currents = solve_transient(circuit,10, .01, show_output=True)
plt.plot(time, np.real(voltages[2]),'k')
plt.grid()
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.show()



