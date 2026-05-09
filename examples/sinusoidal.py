import matplotlib.pyplot as plt

from impulso import *


plt.rcParams['axes.xmargin'] = 0


V1 = SinusoidalVoltageSource(amplitude=1, frequency=1, phase=0, id='V1')
R1 = Resistor(resistance=1000, id='R1')

circuit = Circuit()
circuit.add(V1,[0,1])
circuit.add(R1,[1,0])

time, voltages, currents = solve_transient(circuit,2, 0.01)
plt.plot(time, voltages[1],'k')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('1 Hz Sinusoidal Voltage Source')
plt.grid()
plt.show()



