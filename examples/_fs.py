import numpy as np
import matplotlib.pyplot as plt
import quantiphy as q

from impulso import Circuit, Resistor, Capacitor, Inductor, DCCurrentSource, MutualInductance, ac_sweep


plt.rcParams["axes.xmargin"] = 0

def XAxis_Formatter(x, pos):
    return q.Quantity(x, "Hz").render(form="si")

circuit = Circuit()

I1 = DCCurrentSource(1e-3, id=1)
Rp = Resistor(10, id='Rp')
Lp = Inductor(2e-6, id='Lp')
Cc = Capacitor(10e-12, id='Cc')
Rc = Resistor(10e3, id='Rc')
Rs1 = Resistor(6, id='Rs1')
Ls1 = Inductor(1.25e-6, id='Ls1')
Ls2 = Inductor(1.25e-6, id='Ls2')
Rs2 = Resistor(6, id='Rs2')
C2 = Capacitor(44.252e-12, id='C2')
RL1 = Resistor(100e3, id='RL1')
RL2 = Resistor(100e3, id='RL2')
K1 = MutualInductance(L1=Lp, L2=Ls1, coupling=0.15)
K2 = MutualInductance(L1=Lp, L2=Ls2, coupling=0.15)
K3 = MutualInductance(L1=Ls1, L2=Ls2, coupling=1)

circuit.add(I1, [0, 1])
circuit.add(Rp,[1, 2])
circuit.add(Lp,[2, 0])
circuit.add(Cc,[1, 3])
circuit.add(Rc,[3, 0])
circuit.add(Rs1,[5, 4])
circuit.add(Ls1,[4, 3])
circuit.add(Ls2,[3, 6])
circuit.add(Rs2,[6, 7])
circuit.add(C2,[5, 7])
circuit.add(RL1,[5, 0])
circuit.add(RL2,[7, 0])
circuit.add_instruction(K1)
circuit.add_instruction(K2)
circuit.add_instruction(K3)

# perform the AC sweep
freqs = np.linspace(1e6, 20e6, 1000)

results = ac_sweep(circuit,freqs)

# collect the results
vout = []
vcenter = []

center = 3
top = 5
bottom = 7

for f in freqs:
    node_v, _ = results[f]
    vout.append(np.abs(node_v[top]) - np.abs(node_v[bottom]))
    vcenter.append(node_v[center])

vout = np.array(vout)
venter = np.array(vcenter)

# plot
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

ax1.plot(freqs, vout, "k")
ax1.axvline(10.7e6, color="k", linestyle="--")
ax1.set_xlabel("Frequency")
ax1.set_ylabel(r"$V_{out}$ (V)")
ax1.xaxis.set_major_formatter(XAxis_Formatter)

ax1.grid()
ax2.plot(freqs, np.angle(vcenter, deg=True), "k--")

plt.show()
