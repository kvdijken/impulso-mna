import numpy as np
import matplotlib.pyplot as plt

from impulso import Circuit, Resistor, Capacitor, DiracDeltaVoltageSource, solve_transient


plt.rcParams['axes.xmargin'] = 0

dt = 1e-4
v1 = 55
r1 = 0.1
c1 = 1

circuit = Circuit()
V1 = DiracDeltaVoltageSource(dt=dt, delay=1, voltage=v1, id='V1')
R1 = Resistor(resistance=r1, id='R1')
C1 = Capacitor(capacitance=c1, id='C1')
circuit.add(V1,[0,1])
circuit.add(R1,[1, 2])
circuit.add(C1,[2, 0])

print(circuit)

time, voltages, currents = solve_transient(circuit, t_stop=2, dt=dt, show_output=True)
plt.plot(time, np.real(voltages[2]),'k')
plt.suptitle('Voltage across capacitor')
plt.title(f'R={r1} Ohms, C={c1} F, Voltage pulse = {v1}V Dirac Delta pulse')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.grid()
plt.show()

