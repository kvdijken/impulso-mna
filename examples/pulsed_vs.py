import matplotlib.pyplot as plt

from impulso import *


plt.rcParams['axes.xmargin'] = 0


V1 = PulseVoltageSource(v1=0,
                        v2=1,
                        delay=2,
                        rise_time=0,
                        fall_time=0,
                        pulse_width=0.5,
                        period=1,
                        id='V1')
R1 = Resistor(resistance=1000, id='R1')

circuit = Circuit()
circuit.add(V1,[0,1])
circuit.add(R1,[1,0])

time, voltages, currents = solve_transient(circuit, 5, 0.01, show_output=True)
plt.plot(time, voltages[1],'k')
plt.title('Pulsed Voltage Source')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.grid()
plt.show()



