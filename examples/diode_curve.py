import matplotlib.pyplot as plt
import numpy as np

from impulso import *

plt.rcParams['axes.xmargin'] = 0

V1 = DCVoltageSource(voltage=1, id='V1')
R1 = Resistor(resistance=0.568, id='R1')
D1 = Diode(id='D1')
D1.set_diode_limiter(10)
circuit = Circuit()
circuit.add(V1, [0, 1])
circuit.add(R1, [1, 2])
circuit.add(D1, [2, 0])

print(circuit)

v_ = np.linspace(-.1, 1, 100)
v, i = dc_sweep(circuit, V1, v_, show_output=True)

vd_ = magify(v_pivot(v)[2])
id_ = magify(i_pivot(i)[D1])

plt.plot(np.abs(vd_),np.abs(id_),'k') # type: ignore
plt.xlabel('Vd (V)')
plt.ylabel('Id (A)')
plt.title('Diode I-V Curve')
plt.grid()
plt.show()
