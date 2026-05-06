import matplotlib.pyplot as plt
import numpy as np

from impulso import Circuit, NPN, Resistor, Capacitor, DCVoltageSource, SinusoidalVoltageSource, solve_transient


plt.rcParams['axes.xmargin'] = 0


Q1 = NPN(id='Q1')
R1 = Resistor(9000, id='R1')
R2 = Resistor(1000, id='R2')
Rc = Resistor(3000, id='Rc')
Re = Resistor(100, id = 'Re')
C1 = Capacitor(1e-6, id='C1')
Vcc = DCVoltageSource(10, id='Vcc')
Vin = SinusoidalVoltageSource(.1, 1000, id='Vin')

circuit = Circuit()
circuit.add(Q1, [5,3,4])
circuit.add(R1, [1,3])
circuit.add(R2, [3,0])
circuit.add(Rc, [1,4])
circuit.add(Re, [5,0])
circuit.add(Vcc, [0,1])
circuit.add(Vin, [0,2])
circuit.add(C1, [2,3])

t, v, c = solve_transient(circuit, t_stop=0.005, dt=0.000005)

fig, ax = plt.subplots()
ax2 = ax.twinx()

v3 = np.array(v[3])
v4 = np.array(v[4])
ic = np.array(c[Q1]) # emitter-base-collector currents
ic = -ic[:,2] # # only collector current

ax.plot(t, v4, 'k', label='Vc')
ax.plot(t, v3, 'k--', label='Vb')
ax2.plot(t, ic, 'k--', label='Ic')
ax.grid()
ax.legend()
plt.show()


