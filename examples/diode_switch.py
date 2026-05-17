# see: https://forum.digikey.com/t/operation-of-a-diode-based-rf-switch-a-pin-diode-demonstration/36786

import matplotlib.pyplot as plt

from impulso import (
    Circuit,
    Diode,
    PulseVoltageSource,
    solve_transient,
    Resistor,
    SinusoidalVoltageSource,
    Capacitor
)

plt.rcParams['axes.xmargin'] = 0

vdc = 100
vac = 0.25
rdc = 10_000
rl = 10_000
c1 = 0.001e-6
c2 = 0.0001e-6
f = 2e6

stop = 1000/f
dt = stop / 10_000

pulse_period = 500/f
tr = 20/f

Vdc = PulseVoltageSource(id='Vdc',
                         v1=0,
                         v2=vdc,
                         delay=0,
                         rise_time=tr,
                         fall_time=tr,
                         pulse_width=pulse_period/2,
                         period=pulse_period)
Vac = SinusoidalVoltageSource(amplitude=vac, frequency=f, id='Vac')
R1 = Resistor(resistance=rdc, id='R1')
R2 = Resistor(resistance=rdc, id='R2')
R3 = Resistor(resistance=rl, id='R3')
C1 = Capacitor(capacitance=c1,  id='C1', initial_voltage=0)
C2 = Capacitor(capacitance=c2, id='C2', initial_voltage=0)
D1 = Diode(id='D1') # switching diode
D2 = Diode(id='D2') # clamp diode
D3 = Diode(id='D3') # clamp diode

ckt = Circuit(ground_node=0)

# Provide DC current path for the diode and set operating point
ckt.add(Vdc, [0, 1])
ckt.add(R1, [1, 2])
ckt.add(D1, [2, 3])
ckt.add(R2, [3, 0])

# Add AC source and capacitors for transient response
ckt.add(Vac, [0, 4])
ckt.add(C1, [4, 2])
ckt.add(C2, [3, 5])
ckt.add(R3, [5, 0]) # load for AC response
ckt.add(D2, [5, 0]) # clamping diode
ckt.add(D3, [0, 5]) # clamping diode

times, voltages, currents = solve_transient(ckt, t_stop=stop, dt=dt)


fig, ax = plt.subplots()
ax2 = ax.twinx()
ax.plot(times, voltages[5], 'C0', label=r'$V_{out}$', alpha = 0.75)
ax2.plot(times, voltages[1], 'C1', label=r'$V_{on}$', alpha=0.5)
ax.grid()
ax.set_xlabel('Time (s)')
ax.set_ylabel('Voltage (V)')
plt.title('Transient Response of Diode Switching Circuit')
ax.set_ylim(-5*vac, 5*vac)
plt.legend()
plt.show()
