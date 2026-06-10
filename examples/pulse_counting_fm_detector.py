import matplotlib.pyplot as plt

from impulso import Circuit, Diode, Resistor, Capacitor, DCVoltageSource, SinusoidalVoltageSource, NPN, PNP, solve_transient, solve_dc


plt.rcParams['axes.xmargin'] = 0

Vcc = DCVoltageSource(voltage=9, id='Vcc')
Vin = SinusoidalVoltageSource(amplitude=.5, dc=8, frequency=2000, id='Vin')
R9 = Resistor(resistance=150, id='R9')
Q4 = NPN(id='Q4')
C5 = Capacitor(capacitance=470e-12, id='C5')
D1 = Diode(id='D1')
Q5 = NPN(id='Q5',alpha_f=0.999)
R10 = Resistor(resistance=4700, id='R1')

Q3 = PNP(id='Q3')
R8 = Resistor(resistance=30_000, id='R8')
R7 = Resistor(resistance=4700, id='R7')

circuit = Circuit(ground_node='GND')

circuit.add(Vcc, ['GND', 'VCC'])
circuit.add(Vin, ['GND', 'Q3_B'])
circuit.add(Q3, ['VCC', 'Q3_B', 'Q3_C'])
circuit.add(R8, ['Q3_B', 'Q3_C'])
circuit.add(R7, ['Q3_C', 'GND'])
circuit.add(Q4, ['Q4_E', 'Q3_C', 'VCC'])
circuit.add(C5, ['Q4_E', 'Q5_E'])
circuit.add(R9, ['Q4_E', 'GND'])
circuit.add(D1, ['Q5_E', 'GND'])
circuit.add(Q5, ['Q5_E', 'GND', 'Q5_C'])
circuit.add(R10, ['VCC','Q5_C'])

print(circuit)

dc = solve_dc(circuit)
t, v, i = solve_transient(circuit,t_stop=0.001, dt=0.000005, show_output=True)

fig, ax = plt.subplots()
ax2 = ax.twinx()
ax.plot(t, v['Q3_B'], color='C1', label='IN')
ax2.plot(t, v['Q5_C'], color='C0', label='Q5_C')
ax.legend()
plt.grid()
plt.show()


