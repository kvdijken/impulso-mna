import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['axes.xmargin'] = 0

from impulso import *


I1 = SinusoidalCurrentSource(amplitude=1, frequency=10.7e6, id='I1')
R1 = Resistor(resistance=1000, id='R1')

circuit = Circuit()
circuit.add(I1, [0,1])
circuit.add(R1, [1,0])

print(circuit)

t,v,i = solve_transient(circuit, t_stop=1e-6, dt=1e-9, show_output=True)
v1 = np.real(v[1])

plt.plot(t,i[R1],'k')
plt.grid()
plt.show()

