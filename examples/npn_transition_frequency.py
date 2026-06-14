import numpy as np
import matplotlib.pyplot as plt

from impulso import (
    Circuit,
    Resistor,
    Capacitor,
    NPN,
    DCVoltageSource,
    SinusoidalVoltageSource,
    solve_ac,
    freq_pivot_and_select
)


plt.rcParams['axes.xmargin'] = 0


Vcc = DCVoltageSource(voltage=9, id='Vcc')
Vin = SinusoidalVoltageSource(amplitude=.1, ac_source=True, id='Vin')
C1 = Capacitor(capacitance=1e-6, id='C1')
R1 = Resistor(resistance=8000, id='R1')
R2 = Resistor(resistance=1000, id='R2')
Rc = Resistor(resistance=3000, id='Rc')
Re = Resistor(resistance=1000, id='Re')
Q1 = NPN(id='Q1')

circuit = Circuit(ground_node='GND')
circuit.add(Vcc, ['GND', 'VCC'])
circuit.add(Vin, ['GND', 'VIN'])
circuit.add(C1, ['VIN', 'Q1_B'])
circuit.add(R1, ['VCC', 'Q1_B'])
circuit.add(R2, ['Q1_B', 'GND'])
circuit.add(Rc, ['VCC', 'Q1_C'])
circuit.add(Re, ['Q1_E', 'GND'])
circuit.add(Q1, ['Q1_E', 'Q1_B', 'Q1_C'])

print(circuit)

freqs = np.logspace(1, 10, 500)
results = solve_ac(circuit,freqs,show_output=True) # type: ignore

freqs, node_voltages, _c = freq_pivot_and_select(results, # type: ignore
                                            voltage_nodes=['Q1_C'],
                                            current_components=[Q1],
                                            to_return='MP')
vout = node_voltages['Q1_C'][0]
phase = node_voltages['Q1_C'][1]

fig, axL = plt.subplots()
axR = axL.twinx()
plt.title('Frequency response of NPN transistor amplifier')
axL.plot(freqs,vout,'k')
axL.grid()
axR.plot(freqs,phase,'k--')
# Collector current:
#axR.plot(freqs,_c[Q1][1][:,2],'r')
axL.set_xscale('log')
axL.set_xlabel('Frequency (Hz)')
axL.set_ylabel('Voltage at Q1_C (V)')
plt.show()

