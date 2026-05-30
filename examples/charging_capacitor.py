import numpy as np
import matplotlib.pyplot as plt

from impulso import Circuit, Capacitor, DCCurrentSource, solve_transient

# Define components
C1 = Capacitor(capacitance=1e-6, id='C1', initial_voltage=0)
I1 = DCCurrentSource(current=1e-3, id='I1')

# Define node labels
GND = 'gnd'
N1 = 'n1'

# Create circuit and add components
ckt = Circuit(ground_node=GND)
ckt.add(I1, [GND, N1])
ckt.add(C1, [N1, GND])

# Solve transient response
t, v, i = solve_transient(ckt, t_stop=5e-3, dt=1e-5)

# Plot results
plt.plot(t, v[N1], 'k', label='Voltage at N1')
plt.grid()
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Charging Capacitor')
plt.show()

