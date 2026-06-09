import matplotlib.pyplot as plt
import numpy as np

from quantiphy import Quantity

from impulso import *


plt.rcParams['axes.xmargin'] = 0


V1 = SinusoidalVoltageSource(amplitude=1, frequency=1, phase=0, id='V1')
R1 = Resistor(resistance=1000, id='R1')
C1 = Capacitor(capacitance=1e-3, id='C1', initial_voltage=-2)

circuit = Circuit()
circuit.add(V1,[0,1])
circuit.add(R1,[1,2])
circuit.add(C1,[2,0])


time, voltages, currents = solve_transient(circuit, 10, .01, show_output=True)
plt.plot(time, np.real(voltages[2]),'k')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.suptitle('Sinusoidal Voltage Source with RC Load')
plt.title(f'R={Quantity(R1.resistance,"Ω").render()}, C={Quantity(C1.capacitance,"F").render()}, Initial capacitor voltage={Quantity(C1.initial_voltage,"V").render()}')
plt.grid()
plt.show()



