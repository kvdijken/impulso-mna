# Test current as function of voltage over a diode
# Testing thew soft limiter of the diode


import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['axes.xmargin'] = 0

from impulso import dc_sweep, DCVoltageSource, Diode, Circuit
from impulso.pivot import i_pivot, magify


# Create a simple circuit with a voltage source and a diode
circuit = Circuit(ground_node='GND')
V1 = DCVoltageSource(voltage=1, id='V1')  # 1V source
D1 = Diode(id='D1')

circuit.add(V1, ['GND', 'N1'])
circuit.add(D1, ['N1', 'GND'])

print(circuit)

# Perform a DC sweep from 0V to 1V
v1_ = np.linspace(0, 1, 1000)
voltages, currents = dc_sweep(circuit, V1, v1_, show_output=True)
id_ = magify(i_pivot(currents)['D1'])
iv1_ = magify(i_pivot(currents)['V1'])

# Plot the I-V curve
plt.figure()
plt.plot(v1_, id_,'k', label='Diode Current')
plt.plot(v1_, iv1_,'r--', label='Voltage Source Current')
plt.title('Diode I-V Curve')
plt.xlabel('Voltage (V)')
plt.ylabel('Current (A)')
plt.grid()
plt.legend()
plt.show()

