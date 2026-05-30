import numpy as np
import matplotlib.pyplot as plt

from impulso import Circuit, Capacitor, DCCurrentSource, DCVoltageSource, solve_transient

# Define components
V1 = DCVoltageSource(voltage=9, id='V1')
C1 = Capacitor(capacitance=1e-6, id='C1', initial_voltage=0)
I1 = DCCurrentSource(current=1e-3, id='I1')

# Define node labels
GND = 'gnd'
VCC = 'vcc'
N1 = 'n1'

# Create circuit and add components
ckt = Circuit(ground_node=GND)
ckt.add(V1, [GND, VCC])
ckt.add(C1, [VCC, N1])
ckt.add(I1, [N1, GND])

# Solve transient response
t, v, i = solve_transient(ckt, t_stop=5e-3, dt=1e-5)

# Plot results
plt.plot(t, v[N1], 'k', label='Voltage at N1')
plt.grid()
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Charging Capacitor')
plt.show()

