import matplotlib.pyplot as plt
import numpy as np

from impulso import Circuit, Capacitor, Resistor, SinusoidalVoltageSource, ac_sweep


plt.rcParams['axes.xmargin'] = 0


Vin = SinusoidalVoltageSource(amplitude=1, id='Vin', ac_source=True)
C1 = Capacitor(capacitance=1e-6, id='C1')
R1 = Resistor(resistance=1e3, id='R1')

circuit = Circuit(ground_node=0)
circuit.add(Vin, [0, 1])
circuit.add(C1, [1, 2])
circuit.add(R1, [2, 0])

f_ = np.logspace(1, 6, 1000)
results = ac_sweep(circuit, f_)

vout = []
for f in f_:
    v, i = results[f]
    vout.append(v[2])
vout = np.array(vout)

fig, axL = plt.subplots()
axR = axL.twinx()
axL.plot(f_,np.abs(vout),'k')
axR.plot(f_,np.angle(vout,deg=True),'k--')
axL.grid()
axL.set_xlabel('Frequency (Hz)')
axL.set_ylabel('Magnitude (V)')
axR.set_ylabel('Phase (degrees)')
plt.suptitle('RC Highpass Filter Response')
plt.title('R=1kΩ, C=1μF')
plt.xscale('log')
plt.show()
