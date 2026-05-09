from impulso import *
import numpy as np


D1 = Diode(id='D1', n=1.752, Is=2.52e-9)
R1 = Resistor(resistance=1000, id='R1')
V1 = DCVoltageSource(voltage=1, id='V1')

circuit = Circuit()
circuit.add(V1, [0, 1])
circuit.add(R1, [1, 2])
circuit.add(D1, [2, 0])

voltages, currents = solve_dc(circuit)

v2 = voltages[2]
print("Voltage 2:", np.real(v2))

id = currents['D1']
print("Diode current:", np.real(id))

ir = currents['R1']
print("Resistor current:", np.real(ir))
