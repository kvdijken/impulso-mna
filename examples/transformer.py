# Transient analysis of a transformer circuit with mutual inductance = 0.5
# and dots on opposite sides of the inductors.

import matplotlib.pyplot as plt
import pickle

from impulso import Circuit, Resistor, Inductor, MutualInductance, SinusoidalVoltageSource, solve_transient

# Create the circuit
circuit = Circuit()
Rs = Resistor(resistance=1, id='Rs')
L1 = Inductor(inductance=1e-3, id='L1')
L2 = Inductor(inductance=1e-3, dot_at_node1=False, id='L2')
K1 = MutualInductance(coupling=0.5, id='K1', L1=L1, L2=L2)
V1 = SinusoidalVoltageSource(amplitude=1, frequency=50, id='V1')
R1 = Resistor(resistance=1e3, id='R1')
circuit.add(V1, [0, '1a'])
circuit.add(Rs, ['1a',1])
circuit.add(L1, [1, 0])
circuit.add(L2, [2, 0])
circuit.add(R1, [2, 0])
circuit.add_instruction(K1)

time, voltages, currents = solve_transient(circuit, t_stop=0.1, dt=1e-4)
# Plot the results
plt.plot(time, voltages[1], label='Voltage across L1')
plt.plot(time, voltages[2], label='Voltage across L2')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Transient Analysis of Transformer Circuit')
plt.legend()
plt.grid()
plt.show()

with open('data.pickle', 'wb') as f:
    pickle.dump((time, voltages, currents), f, pickle.HIGHEST_PROTOCOL)
