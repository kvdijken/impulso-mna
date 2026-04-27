import matplotlib.pyplot as plt
import numpy as np

from impulso import *

plt.rcParams['axes.xmargin'] = 0

@np.vectorize
def current(v):
    V1 = DCVoltageSource(v, id='V1')
    R1 = Resistor(0.568, id='R1')
    D1 = Diode(id='D1', n=1.752, Is=2.52e-9)
    circuit = Circuit()
    circuit.add(V1, [0, 1])
    circuit.add(R1, [1, 2])
    circuit.add(D1, [2, 0])
    v, i = solve_dc(circuit)
    return v[2], i[D1]

v_ = np.linspace(-.1, 1, 100)
data = current(v_)
vd_, id_ = data[0], data[1]

plt.plot(vd_,id_,'k')
plt.xlabel('Vd (V)')
plt.ylabel('Id (A)')
plt.title('Diode I-V Curve')
plt.grid()
plt.show()
    