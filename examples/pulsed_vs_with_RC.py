import matplotlib.pyplot as plt
import numpy as np

from impulso import *


plt.rcParams['axes.xmargin'] = 0

V1 = PulseVoltageSource(0,1,4.5,0.2,0.2,0.5,1,id='V1')
R1 = Resistor(50, id='R1')
C1 = Capacitor(1e-3,id='C1',initial_voltage=-0.5)

circuit = Circuit()
circuit.add(V1,[0,1])
circuit.add(R1,[1,2])
circuit.add(C1,[2,0])

time, voltages, currents = solve_transient(circuit,10, .01)
plt.plot(time, np.real(voltages[2]),'k')
plt.grid()
plt.show()



