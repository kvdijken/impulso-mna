import numpy as np
import matplotlib.pyplot as plt

from impulso import Circuit, Resistor, NPN, Capacitor, DCVoltageSource, solve_transient

plt.rcParams['axes.xmargin'] = 0


# Define components
V1 = DCVoltageSource(voltage=9, id='V1')
R1 = Resistor(resistance=1e3, id='R1')
R2 = Resistor(resistance=10e3, id='R2')
R3 = Resistor(resistance=10e3, id='R3')
Q1 = NPN(id='Q1')
C1 = Capacitor(capacitance=10e-9, id='C1', initial_voltage=0)

# Define node labels
GND = 'gnd'
B = 'b'
C = 'c'
E = 'e'
VCC = 'vcc'

# Create circuit and add components
ckt = Circuit(ground_node=GND)
ckt.add(V1, [GND, VCC])
ckt.add(R1, [GND, B])
ckt.add(R2, [B, VCC])
ckt.add(R3, [GND, E])
ckt.add(Q1, [E, B, C])
ckt.add(C1, [C, VCC])

# Solve transient response
t, v, i = solve_transient(ckt, t_stop=1e-3, dt=1e-7)

# Plot results
plt.plot(t, v[C], 'k', label='Vout')
plt.grid()
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.show()


# After the first solve_mna in the loop in solve_transient, the voltage at node C is 18V,
# which is incorrect. This should be 9V. This is because the initial voltage across
# the capacitor is not being set correctly in the first iteration of the transient
# analysis. The initial voltage should be set based on the initial conditions of
# the circuit, which in this case is 0V across the capacitor.

