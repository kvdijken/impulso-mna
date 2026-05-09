import matplotlib.pyplot as plt
import numpy as np

from impulso import Circuit, Diode, Resistor, Capacitor, SinusoidalVoltageSource, solve_transient

plt.rcParams['axes.xmargin'] = 0

V1 = SinusoidalVoltageSource(amplitude=1, frequency=3, phase=np.pi/2, id='V1')
R1 = Resistor(resistance=1000, id='R1')
C1 = Capacitor(capacitance=1e-2, id='C1')
D1 = Diode(id='D1', n=1.752, Is=2.52e-9)

circuit = Circuit()
circuit.add(V1, [0, 1])
circuit.add(D1, [1, 2])
circuit.add(R1, [2, 0])
circuit.add(C1, [2, 0])

t, v, i = solve_transient(circuit,t_stop=2, dt=0.001)
plt.plot(t, np.real(v[1]),'k--',lw=.75,label='Voltage at node 1')
plt.plot(t, np.real(v[2]),'k',label='rectified at node 2')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Half-wave Rectifier')
plt.grid()
plt.legend()
plt.show()

