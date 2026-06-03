import numpy as np
import matplotlib.pyplot as plt

from impulso import Circuit, Resistor, NPN, PNP, Capacitor, DCVoltageSource, solve_transient, emitter_current

plt.rcParams['axes.xmargin'] = 0

# Define components
R1 = Resistor(resistance=1e3, id='R1')
R2 = Resistor(resistance=10e3, id='R2')
R3 = Resistor(resistance=10e3, id='R3')
R4 = Resistor(resistance=10e3, id='R4')
R5 = Resistor(resistance=10e3, id='R5')
#Q1 = PNP(id='Q1',cbc=0,cbe=0)
#Q2 = PNP(id='Q2',cbc=0,cbe=0)
#Q3 = NPN(id='Q3',cbc=0,cbe=0)
Q1 = PNP(id='Q1')
Q2 = PNP(id='Q2')
Q3 = NPN(id='Q3')
C1 = Capacitor(capacitance=10e-9, id='C1', initial_voltage=-3)
V1 = DCVoltageSource(voltage=9, id='V1')

# Define circuit and add components
ckt = Circuit(ground_node=0)
ckt.add(V1, [0, 1])
ckt.add(R1, [1, 2])
ckt.add(R2, [2, 0])
ckt.add(R3, [1, 3])
ckt.add(Q1, [3, 2, 4])
ckt.add(C1, [4, 0])
ckt.add(Q2, [4, 5, 6])
ckt.add(Q3, [0, 6, 5])
ckt.add(R4, [1, 5])
ckt.add(R5, [5, 0])

# Solve transient response
t, v, i = solve_transient(ckt, t_stop=1e-3, dt=1e-6)

OUT = 4

# Plot results
fig, axL = plt.subplots()
axR = axL.twinx()
axL.plot(t, v[OUT], 'k', label=f'V({OUT})')
axR.plot(t, v[6], 'r', label='V(6)')
#axR.plot(t, emitter_current(i[Q3]), 'r', label='I(Q1)')
axL.grid()
axL.set_xlabel('Time (s)')
axL.set_ylabel('Voltage (V)')
#plt.legend()
plt.show()
