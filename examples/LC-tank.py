import numpy as np
import matplotlib.pyplot as plt

from quantiphy import Quantity

from impulso import Circuit, Capacitor, Inductor, solve_transient
from impulso import Resistor

plt.rcParams['axes.xmargin'] = 0


l1 = 1e-3
c1 = 1e-6

L1 = Inductor(l1, id='L1', initial_current=1e-3)
C1 = Capacitor(c1, id='C1')

circuit = Circuit()
circuit.add(C1, [1, 0])
circuit.add(L1, [0, 1])

t_stop = .001
t, v, i = solve_transient(circuit,t_stop=t_stop, dt=t_stop/1000)

plt.plot(t, np.real(v[1]),'k',label='Voltage at node 1')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.suptitle('Resonating LC Tank Circuit')
plt.title(f'L={Quantity(l1,"H").render()}, C={Quantity(c1,"F").render()}, Initial current={Quantity(L1.initial_current,"A").render()}')
plt.grid()
plt.show()
