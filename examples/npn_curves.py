import matplotlib.pyplot as plt
import numpy as np

from labellines import labelLines

from impulso import profile, NPN, Circuit, DCVoltageSource, DCCurrentSource, solve_dc

plt.rcParams['axes.xmargin'] = 0


GROUND = 0

def circuit(ib:float, vce: float) -> Circuit:
    npn = NPN(id='Q1')
    is_b = DCCurrentSource(ib, id='Ib')
    vs_ce = DCVoltageSource(vce,id='Vce')

    emitter = GROUND
    base = 1
    collector = 2
    
    c = Circuit(ground_node=GROUND)
    c.add(npn, [emitter, base, collector])
    c.add(is_b, [GROUND,base])
    c.add(vs_ce, [GROUND,collector])
    return c


@profile
def main():
    ib_ = np.linspace(0, 0.1, 10) # base current in mA
    vce_ = np.linspace(0, 4.5, 100) # collector-emitter voltage in V

    for ib in ib_:
        ic = []
        for vce in vce_:
            c = circuit(ib/1000,vce)
            v, i = solve_dc(c)
            ic.append(-np.real(i['Q1'][2])*1000)
        plt.plot(vce_, ic, 'k', lw=0.75, label=f"Ib={ib:.2f}mA")    

    plt.grid()
    plt.title('NPN Transistor Output Characteristics')
    plt.xlabel(f'Vce (V)')
    plt.ylabel(f'Ic (mA)')
    labelLines(plt.gca().get_lines())

if __name__ == "__main__":
    main()
    plt.show()
