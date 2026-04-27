import matplotlib.pyplot as plt
import numpy as np

from impulso import *


plt.rcParams['axes.xmargin'] = 0

V1 = SinusoidalVoltageSource(1,1,0,id='V1')
V2 = PulseVoltageSource(0,2,0,0,0,0.3,0.5,id='V2')
R1 = Resistor(1000, id='R1')
C1 = Capacitor(1e-3,id='C1',initial_voltage=-2)

circuit = Circuit()
circuit.add(V1,[0,1])
circuit.add(V2,[1,2])
circuit.add(R1,[2,3])
circuit.add(C1,[3,0])

time, voltages, currents = solve_transient(circuit,10, .01)
plt.plot(time, np.real(voltages[3]),'k')
plt.grid()
plt.show()

