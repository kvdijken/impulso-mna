import numpy as np
import impulso as bia
import matplotlib.pyplot as plt
import quantiphy as q
from impulso import solve_ac, SinusoidalCurrentSource, Resistor, Inductor, Capacitor, MutualInductance, DCVoltageSource

plt.rcParams["axes.xmargin"] = 0

def XAxis_Formatter(x, pos):
    return q.Quantity(x, "Hz").render(form="si")

f = 10.7e6

top = 5
bottom = 7


@np.vectorize
def c2_f(cc: float) -> float:
    
    I1 = SinusoidalCurrentSource(1e-3, ac_source=True, id='I1')
    Rp = Resistor(10, id='Rp')
    Lp = Inductor(2e-6, id='Lp')
    Cc = Capacitor(cc, id='Cc')
    Rc = Resistor(10e3, id='Rc')
    Rs1 = Resistor(6, id='Rs1')
    Ls1 = Inductor(1.25e-6, id='Ls1')
    Ls2 = Inductor(1.25e-6, id='Ls2')
    Rs2 = Resistor(6, id='Rs2')
    RL1 = Resistor(100e3, id='RL1')
    RL2 = Resistor(100e3, id='RL2')
    K1 = MutualInductance(L1=Lp, L2=Ls1, coupling=0.15)
    K2 = MutualInductance(L1=Lp, L2=Ls2, coupling=0.15)
    K3 = MutualInductance(L1=Ls1, L2=Ls2, coupling=1)
    V2 = DCVoltageSource(0, id='V2')

    circuit = bia.Circuit()
    circuit.add(I1, [0, 1])
    circuit.add(Rp,[1, 2])
    circuit.add(Lp, [2, 0])
    circuit.add(Cc, [1, 3])
    circuit.add(Rc, [3, 0])
    circuit.add(Rs1, [5, 4])
    circuit.add(Ls1, [4, 3])
    circuit.add(Ls2, [3, 6])
    circuit.add(Rs2, [6, 7])
    circuit.add(RL1, [5, 0])
    circuit.add(RL2, [7, 0])
    circuit.add_instruction(K1)
    circuit.add_instruction(K2)
    circuit.add_instruction(K3)
    
    voltages, currents = solve_ac(circuit,f)

    # Calculate open circuit voltage
    Vtop = voltages[top]
    Vbottom = voltages[bottom]
    Voc = Vtop - Vbottom

    # Calculate short circuit current
    circuit.add(V2,[top,bottom])
    voltages, currents = solve_ac(circuit,f)
    Isc = currents[V2]
    Z = Voc / Isc
    X = np.imag(Z)
    C2 = 1 / (2 * np.pi * f * X)

    return C2

@np.vectorize
def phase(cc: float,c2: float) -> float:
    circuit = bia.Circuit()

    I1 = SinusoidalCurrentSource(1e-3, id=1, ac_source=True)
    Rp = Resistor(10, id='Rp')
    Lp = Inductor(2e-6, id='Lp')
    Cc = Capacitor(cc, id='Cc')
    Rc = Resistor(10e3, id='Rc')
    Rs1 = Resistor(6, id='Rs1')
    Ls1 = Inductor(1.25e-6, id='Ls1')
    Ls2 = Inductor(1.25e-6, id='Ls2')
    Rs2 = Resistor(6, id='Rs2')
    C2 = Capacitor(c2, id='C2')
    RL1 = Resistor(100e3, id='RL1')
    RL2 = Resistor(100e3, id='RL2')
    K1 = MutualInductance(L1=Lp, L2=Ls1, coupling=0.15)
    K2 = MutualInductance(L1=Lp, L2=Ls2, coupling=0.15)
    K3 = MutualInductance(L1=Ls1, L2=Ls2, coupling=1)

    circuit.add(I1, [0, 1])
    circuit.add(Rp,[1, 2])
    circuit.add(Lp, [2, 0])
    circuit.add(Cc, [1, 3])
    circuit.add(Rc, [3, 0])
    circuit.add(Rs1, [5, 4])
    circuit.add(Ls1, [4, 3])
    circuit.add(Ls2, [3, 6])
    circuit.add(Rs2, [6, 7])
    circuit.add(C2, [5, 7])
    circuit.add(RL1, [5, 0])
    circuit.add(RL2, [7, 0])
    circuit.add_instruction(K1)
    circuit.add_instruction(K2)
    circuit.add_instruction(K3)
    
    response = solve_ac(circuit,f)
    Vcenter = response[0][3]
    phi = np.angle(Vcenter, deg=True)
    
    return phi


cc_ = np.logspace(-12,-9,1000)
c2_ = c2_f(cc_)

fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

ax1.plot(cc_*1e12, c2_*1e12,'k')
ax1.set_xlabel(f'$C_c$ (pF)')
ax1.set_ylabel(f'$C_2$ (pF)')
ax1.grid()
ax1.set_xscale('log')
ax2.plot(cc_*1e12, phase(cc_, np.abs(c2_)),'k--')
ax2.set_ylabel(f'Centertap phase (degrees)')

plt.show()