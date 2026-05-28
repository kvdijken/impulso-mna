import numpy as np
import matplotlib.pyplot as plt

from impulso import Circuit, Diode, Resistor, SinusoidalVoltageSource, Opamp, solve_transient


plt.rcParams['axes.xmargin'] = 0

R1 = Resistor(resistance=1e3,id='R1')
V1 = SinusoidalVoltageSource(amplitude=1, frequency=1000, id='V1')
OA1 = Opamp(id='OA1')
D1 = Diode(id='D1')
D1.DIODE_LIMITER_NVT = 100  # Use a more aggressive limiter for better convergence in this test

gnd = 0
pos = 1
neg = 2
out = 3

circuit = Circuit(ground_node=gnd)
circuit.add(V1, [gnd, pos])
circuit.add(OA1, [pos, neg, out])
circuit.add(D1, [out, neg])
circuit.add(R1, [neg, gnd])

stop = 0.005
t = np.linspace(0, stop, 1000)
t,v,c, = solve_transient(circuit,
                         t_stop=stop,
                         dt=stop/1000)

plt.plot(t, v[pos], label="Input voltage")
plt.plot(t, v[neg], label="Output voltage")
plt.grid()
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.title("Ideal Diode with opamp and diode")
plt.legend()
plt.show()
