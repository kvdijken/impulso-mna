import numpy as np
import pytest

from impulso import *

# TODO Write test for inductor initial current, can take LC_tank.py for that


def within(value, tobe, perc):
    ratio = value / tobe
    perc = perc / 100
    return (ratio > 1-perc) and (ratio < 1+perc)




def print_currents_voltages(circuit, voltages, currents):
    for c in currents.keys():
        if not isinstance(c,Component):
            print('current',c,':',currents[c])
    for n in circuit.all_nodes():
        print('voltage node',n,':',voltages[n])


class Test_general:

    def test_1(self):
        # Test the within function
        assert(within(1.00099, 1, 0.1))

    def test_2(self):
        # Test the within function with a value that is outside the range
        assert(not within(1.0011, 1, 0.1))

    def test_3(self):
        # Test if a negative resistance is caught
        with pytest.raises(ValueError):
            R1 = Resistor(-1)

    def test_4(self):
        # Test if a negative capacitance is caught
        with pytest.raises(ValueError):
            C1 = Capacitor(-1)

    def test_5(self):
        # Test if a negative inductance is caught
        with pytest.raises(ValueError):
            I1 = Inductor(-1)

    def test_6(self):
        # Test if a coupling factor outside < 0 is caught
        L1 = Inductor(1e-3)
        L2 = Inductor(1e-3)
        with pytest.raises(ValueError):
            K1 = MutualInductance(L1, L2, -1)
        # Test if a coupling factor outside > 1 is caught
        with pytest.raises(ValueError):
            L1 = Inductor(1e-3)
            L2 = Inductor(1e-3)
            K1 = MutualInductance(L1, L2, +2)


class Test_Circuit:

    def test_1(self):
        # Test if a circuit with no components can be simulated
        circuit = Circuit()
        with pytest.raises(TopologyError):
            result = solve_dc(circuit)

    def test_2(self):
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1)
        R1 = Resistor(1e3)
        R2 = Resistor(1e3)
        circuit.add(V1,[0, 1])
        circuit.add(R1,[1, 0])
        circuit.add(R2,[2, 3])
        with pytest.raises(np.linalg.LinAlgError):
            result = solve_dc(circuit)

    def test_3(self):
        # Loose end resistor, other end connected to ground
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1)
        R1 = Resistor(resistance=1e3)
        R2 = Resistor(resistance=1e3)
        circuit.add(V1,[0, 1])
        circuit.add(R1,[1, 0])
        circuit.add(R2,[2, 0])
        nodes, comps = solve_dc(circuit)
        VR2 = nodes[2]
        assert(np.abs(VR2) < 1e-6)
        IR2 = comps[R2.id]
        assert(np.abs(IR2) < 1e-6)

    def test_4(self):
        # test if adding component with illegal nodes list is caught
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1)
        with pytest.raises(TypeError):
            circuit.add(V1, 1) # should be a list of nodes, not a single node

    def test_5(self):
        # test if adding a component with a duplicate ID is caught
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        V2 = DCVoltageSource(voltage=1, id='V1') # duplicate ID
        circuit.add(V1, [0, 1])
        with pytest.raises(TopologyError):
            circuit.add(V2, [1, 2])

    def test_6(self):
        # test if adding a component that is not an instance of Component is caught
        circuit = Circuit()
        with pytest.raises(TypeError):
            circuit.add("not a component", [0, 1])

    def test_7(self):
        # test if a circuit without a component connected to ground is caught
        circuit = Circuit(ground_node=0)
        V1 = DCVoltageSource(voltage=1)
        R1 = Resistor(resistance=1e3)
        circuit.add(V1, [3, 1])
        circuit.add(R1, [1, 2])
        with pytest.raises(TopologyError):
            circuit.validate()

    def test_8(self):
        # test if a circuit with a component connected to ground is valid
        circuit = Circuit(ground_node=0)
        V1 = DCVoltageSource(voltage=1)
        R1 = Resistor(resistance=1e3)
        circuit.add(V1, [0, 1])
        circuit.add(R1, [1, 2])
        circuit.validate()

    def test_10(self):
        # test if we can add a component with only one node
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1)
        circuit.add(V1, [0, 1]) # should be fine

        V2 = DCVoltageSource(voltage=   1)
        with pytest.raises(ValueError):
            circuit.add(V2, [0]) # should raise an error

    def test_11(self):
        # Test if a CCVS with illegal controlling component is caught
        circuit = Circuit()
        CCVS1 = CCVS(rm=2, id='CCVS1')
        circuit.add(CCVS1, [0, 1])

        with pytest.raises(TypeError):
            CCVS1.connect("not a component")

        with pytest.raises(TypeError):
            CCVS1.connect(CCVS1) # should not be able to connect to itself

        R1 = Resistor(1e3, id='R1')
        circuit.add(R1, [1, 0])
        CCVS1.connect(R1) # Should connect to a resistor

        C1 = Capacitor(capacitance=1e-6, id='C1')
        circuit.add(C1, [1, 0])
        CCVS1.connect(C1) # Should connect to a resistor

        V1 = DCVoltageSource(voltage=1, id='V1')
        circuit.add(V1, [1, 0])
        CCVS1.connect(V1) # Should connect to a resistor

        L1 = Inductor(inductance=1e-3, id='L1')
        with pytest.raises(TypeError):
            CCVS1.connect(L1) # should not be able to connect to an inductor


class Test_DC:

    def test_1a(self):
        # 1 volt over a 1kOhm resistor, current should be 1mA
        # test positive direction of current
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,0])
        result = solve_dc(circuit)
        IR1 = result[1][R1.id]
        assert(within(IR1, 0.001, 0.1))

    def test_1b(self):
        # 1 volt over a 1kOhm resistor, current should be 1mA
        # test positive direction of current
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,0])
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        IV1 = currents[V1]
        assert(within(IV1,0.001, 0.1))
        IR1 = currents[R1]
        assert(within(IR1, 0.001, 0.1))

    def test_2(self):
        # 1 volt over a 1kOhm resistor, current should be 1mA
        # test negative direction of current
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(R1,[0,1])
        result = solve_dc(circuit)
        IR1 = result[1][R1.id]
        assert(within(IR1, -0.001, 0.1))

    def test_3(self):
        # 1 volt over a 1kOhm resistor
        # Test node 1 voltage 1 volt
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,0])
        result = solve_dc(circuit)
        VR1 = result[0][1]
        assert(within(VR1, 1.0, 0.1))

    def test_4(self):
        # Two 1 volt voltage sources in series, over a 1kOhm resistor.
        # Should add up to two volts.
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        V2 = DCVoltageSource(voltage=1, id='V2')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(V2,[1,2])
        circuit.add(R1,[2,0])
        result = solve_dc(circuit)
        VR1 = result[0][2]
        assert(within(VR1, 2.0, 0.1))

    def test_5(self):
        # Two 1 volt voltage sources in series, same sign but opposite direction over a 1kOhm resistor.
        # Should add up to zero volts.
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        V2 = DCVoltageSource(voltage=1, id='V2')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(V2,[2,1])
        circuit.add(R1,[2,0])
        result = solve_dc(circuit)
        VR1 = result[0][2]
        assert(VR1<1e-6)

    def test_6(self):
        # Two 1 volt voltage sources in series, same direction but opposite sign over a 1kOhm resistor.
        # Should add up to zero volts.
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        V2 = DCVoltageSource(voltage=-1, id='V2')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(V2,[1,2])
        circuit.add(R1,[2,0])
        result = solve_dc(circuit)
        VR1 = result[0][2]
        assert(VR1<1e-6)

    def test_7(self):
        # 1 volt over a 1kOhm resistor, current should be 1mA
        # test positive direction of current
        # Same as test_1, but check if we can get
        # the current by using the component reference
        # instead of the component id.
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,0])
        result = solve_dc(circuit)
        IR1_1 = result[1][R1.id]
        IR1_2 = result[1][R1]
        assert(IR1_1 == IR1_2)

    def test_8(self):
        # Test a VCVS
        I1 = DCCurrentSource(current=1.7, id='I1')
        I2 = DCCurrentSource(current=0.5, id='I2')
        R1 = Resistor(resistance=1e3, id='R1')
        R2 = Resistor(resistance=1e3, id='R2')
        R3 = Resistor(resistance=1e3, id='R3')
        R4 = Resistor(resistance=1e3, id='R4')
        VCVS1 = VCVS(A=2.5, id='VCVS1')
        circuit = Circuit()
        circuit.add(I1,[0,1])
        circuit.add(R1,[1,0])
        circuit.add(R2,[2,0])
        circuit.add(R3,[2,3])
        circuit.add(R4,[3,0])
        circuit.add(I2,[0,3])
        circuit.add(VCVS1,[2,1,3,2])
        voltages, currents = solve_dc(circuit)
        V12 = voltages[1] - voltages[2]
        V3 = voltages[3]
        Ivcvs = currents[VCVS1]
        print_currents_voltages(circuit, voltages, currents)
        assert(within(V12,233.333,0.1))
        assert(within(V3, 593.333, 0.1))
        assert(within(Ivcvs, -0.7799, 0.1))

    def test_9(self):
        # Test a CCVS with the controlling current through a resistor
        I1 = DCCurrentSource(current=1, id='I1')
        I2 = DCCurrentSource(current=3, id='I2')
        R1 = Resistor(resistance=1e3, id='R1')
        R2 = Resistor(resistance=1e3, id='R2')
        R3 = Resistor(resistance=1e3, id='R3')
        R4 = Resistor(resistance=1e3, id='R4')
        CCVS1 = CCVS(rm=2, id='CCVS1')
        circuit=Circuit()
        circuit.add(I1,[0,1])
        circuit.add(R1,[1,0])
        circuit.add(CCVS1,[2,1])
        circuit.add(R2,[2,0])
        circuit.add(R3,[2,3])
        circuit.add(R4,[3,0])
        circuit.add(I2,[0,3])
        CCVS1.connect(R3)
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        V12 = voltages[1] - voltages[2]
        assert(within(V12, 2, 0.1))

    def test_10(self):
        # Test a CCVS with the controlling current through a zero volt voltage source
        I1 = DCCurrentSource(current=1, id='I1')
        I2 = DCCurrentSource(current=3, id='I2')
        R1 = Resistor(resistance=1e3, id='R1')
        R2 = Resistor(resistance=1e3, id='R2')
        R3 = Resistor(resistance=1e3, id='R3')
        R4 = Resistor(resistance=1e3, id='R4')
        V1 = DCVoltageSource(voltage=0, id='V1')
        CCVS1 = CCVS(rm=2, id='CCVS1')
        circuit = Circuit()
        circuit.add(I1,[0,1])
        circuit.add(R1,[1,0])
        circuit.add(CCVS1,[2,1])
        circuit.add(R2,[2,0])
        circuit.add(R3,[2,3])
        circuit.add(V1,[3,4])
        circuit.add(R4,[4,0])
        circuit.add(I2,[0,4])
        CCVS1.connect(V1)
        voltages, currents = solve_dc(circuit)
        V12 = voltages[1] - voltages[2]
        print_currents_voltages(circuit, voltages, currents)
        print('DC_test_11 V12 = ',V12)
        assert(within(V12, -2, 0.1))

    def tt_11(self):
        # Test a CCCS with the controlling current through a resistor
        I1 = DCCurrentSource(current=1, id='I1')
        I2 = DCCurrentSource(current=3, id='I2')
        R1 = Resistor(resistance=1e3, id='R1')
        R2 = Resistor(resistance=1e3, id='R2')
        R3 = Resistor(resistance=1e3, id='R3')
        R4 = Resistor(resistance=1e3, id='R4')
        V1 = DCVoltageSource(voltage=0, id='V1')
        CCCS1 = CCCS(A=3, id='CCCS1')
        circuit = Circuit()
        circuit.add(I1,[0,1])
        circuit.add(R1,[1,0])
        circuit.add(CCCS1,[1,2])
        circuit.add(R2,[2,0])
        circuit.add(R3,[2,3])
        circuit.add(V1,[3,4])
        circuit.add(R4,[4,0])
        circuit.add(I2,[0,4])
        CCCS1.connect(R3)
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        c12 = currents[CCCS1]
        assert(within(c12, -1.5, 0.1))

    def test_12(self):
        # Test a CCCS with the controlling current through a zero volt voltage source
        I1 = DCCurrentSource(current=1, id='I1')
        I2 = DCCurrentSource(current=3, id='I2')
        R1 = Resistor(resistance=1e3, id='R1')
        R2 = Resistor(resistance=1e3, id='R2')
        R3 = Resistor(resistance=1e3, id='R3')
        R4 = Resistor(resistance=1e3, id='R4')
        V1 = DCVoltageSource(voltage=0, id='V1')
        CCCS1 = CCCS(A=3, id='CCCS1')
        circuit = Circuit()
        circuit.add(I1,[0,1])
        circuit.add(R1,[1,0])
        circuit.add(CCCS1,[2,1])
        circuit.add(R2,[2,0])
        circuit.add(R3,[2,3])
        circuit.add(V1,[3,4])
        circuit.add(R4,[4,0])
        circuit.add(I2,[0,4])
        CCCS1.connect(V1)
        voltages, currents = solve_dc(circuit)
        c12 = currents[CCCS1]
        print_currents_voltages(circuit, voltages, currents)
        assert(within(c12, -1.5, 0.1))

    def test_13(self):
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        V2 = DCVoltageSource(voltage=0, id='V2')
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,2])
        circuit.add(V2,[2,0])
        voltages, currents = solve_dc(circuit)
        for c in currents.keys():
            if not isinstance(c,Component):
                print('DC_test_13 current ',c,':',currents[c])
        for n in circuit.all_nodes():
            print('DC_test_11 voltage node',n,':',voltages[n])
        iV2 = currents[V2]
        assert(within(iV2, 0.001, 0.1))

    def test_14(self):
        I1 = DCCurrentSource(current=0.001, id='I1')
        R1 = Resistor(resistance=1e3, id='R1')
        V2 = DCVoltageSource(voltage=0, id='V2')
        circuit = Circuit()
        circuit.add(I1,[0,1])
        circuit.add(R1,[1,2])
        circuit.add(V2,[2,0])
        voltages, currents = solve_dc(circuit)
        for c in currents.keys():
            if not isinstance(c,Component):
                print('DC_test_14 current ',c,':',currents[c])
        for n in circuit.all_nodes():
            print('DC_test_14 node ',n,':',voltages[n])
        iV2 = currents[V2]
        assert(within(iV2, 0.001, 0.1))

    def test_15_1(self):
        R1 = Resistor(resistance=1e3, id='R1')
        V1 = DCVoltageSource(voltage=1, id='V1')
        R2 = Resistor(resistance=1e3, id='R2')
        circuit = Circuit()
        circuit.add(R1,[0,1])
        circuit.add(V1,[1,2])
        circuit.add(R2,[2,0])
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        assert(within(voltages[1], -0.5, 0.1))
        assert(within(voltages[2], 0.5, 0.1))
        assert(within(currents[R1], 0.0005, 0.1))
        assert(within(currents[R2], 0.0005, 0.1))
        assert(within(currents[V1], 0.0005, 0.1))

    def test_15_2(self):
        R1 = Resistor(resistance=1e3, id='R1')
        V1 = DCVoltageSource(voltage=1, id='V1')
        R2 = Resistor(resistance=1e3, id='R2')
        circuit = Circuit()
        circuit.add(R1,[0,1])
        circuit.add(V1,[2,1])
        circuit.add(R2,[2,0])
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        assert(within(voltages[1], 0.5, 0.1))
        assert(within(voltages[2], -0.5, 0.1))
        assert(within(currents[R1], -0.0005, 0.1))
        assert(within(currents[R2], -0.0005, 0.1))
        assert(within(currents[V1], 0.0005, 0.1))

    def test_16(self):
        V1 = DCVoltageSource(voltage=1, id='V1')
        I1 = DCCurrentSource(current=2, id='I1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(I1,[2,1])
        circuit.add(R1,[2,0])
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        assert(within(voltages[1], 1.0, 0.1))
        assert(within(voltages[2], -2000.0, 0.1))
        assert(within(currents[V1], -2, 0.1))
        assert(within(currents[I1], 2, 0.1))
        assert(within(currents[R1], -2, 0.1))

    def test_18(self):
        # Test current direction through a zero volts voltage source
        V1 = DCVoltageSource(voltage=1, id='V1')
        V2 = DCVoltageSource(voltage=0, id='V2')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,2])
        circuit.add(V2,[2,0])
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        assert(within(voltages[1], 1.0, 0.1))
        assert(voltages[2] < 1e-6)
        assert(within(currents[V1], 0.001, 0.1))
        assert(within(currents[V2], 0.001, 0.1))

    def test_19(self):
        # Test current direction through a zero volts voltage source
        V1 = DCVoltageSource(voltage=1, id='V1')
        V2 = DCVoltageSource(voltage=0, id='V2')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,2])
        circuit.add(V2,[0,2])
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        assert(within(voltages[1], 1.0, 0.1))
        assert(voltages[2] < 1e-6)
        assert(within(currents[V1], 0.001, 0.1))
        assert(within(currents[V2], -0.001, 0.1))

    def test_20(self):
        # Opamp
        V1 = DCVoltageSource(voltage=1, id='V1')
        OA1 = Opamp(id='OA1')
        R1 = Resistor(resistance=1e3, id='R1')
        R2 = Resistor(resistance=1e3, id='R2')

        pos = 1
        neg = 3
        out = 2

        circuit = Circuit()
        circuit.add(V1,[0,pos])
        circuit.add(R1,[out,neg])
        circuit.add(R2,[neg,0])
        circuit.add(OA1,[pos,neg,out]) # order is pos, neg, out

        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        assert(within(voltages[pos], 1.0, 0.1))
        assert(within(voltages[neg], 1.0, 0.1))
        assert(within(voltages[out], 2.0, 0.1))

        # Test output current
        Iout = currents[OA1]
        print('DC_test_20, Iout=',Iout)
        assert(within(Iout, 0.001, 0.1))


    def test_21(self):
        cccs1 = CCCS(A=2, id='CCCS1')
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,0])
        circuit.add(cccs1,[1,0])
        cccs1.connect(R1)
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        assert(within(currents[cccs1], 0.002, 0.1))

    def test_22(self):
        cs1 = DCCurrentSource(current=1, id='CS1')
        v1 = DCVoltageSource(voltage=1, id='V1')
        circuit = Circuit()
        circuit.add(v1,[0,1])
        circuit.add(cs1,[1,0])
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        assert(within(currents[cs1], 1, 0.1))
        assert(within(currents[v1], 1, 0.1))

    def tt_23(self):
        vs_be = DCVoltageSource(voltage=0.6, id='Vbe')
        vs_ce = DCVoltageSource(voltage=9, id='Vce')
        d1 = Diode(id='D1')
        v0 = DCVoltageSource(voltage=0, id='V0')
        cccs1 = CCCS(A=1, id='CCCS1')

        ground = 0
        emitter = ground
        base = 1
        collector = 2
        emitter0 = 3

        circuit = Circuit()
        circuit.add(vs_be, [ground,base])
        circuit.add(d1, [base, emitter0])
        circuit.add(v0, [emitter0, emitter])
        circuit.add(vs_ce, [ground,collector])
        circuit.add(cccs1, [collector, emitter])
        cccs1.connect(v0)

        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)

        assert True

    def test_24(self):
        ''' test NPN in saturation '''
        Q1 = NPN(id='Q1')
        R1 = Resistor(resistance=9000, id='R1')
        R2 = Resistor(resistance=1000, id='R2')
        Rc = Resistor(resistance=5000, id='Rc')
        Re = Resistor(resistance=100, id = 'Re')
        Vcc = DCVoltageSource(voltage=10, id='Vcc')

        circuit = Circuit()
        circuit.add(Q1, [5,3,4])
        circuit.add(R1, [1,3])
        circuit.add(R2, [3,0])
        circuit.add(Rc, [1,4])
        circuit.add(Re, [5,0])
        circuit.add(Vcc, [0,1])

        v, i = solve_dc(circuit)
        print_currents_voltages(circuit, v, i)
        assert(v[4]>0)

    def test_25(self):
        # RL network with 1 volt DC source
        # Run with AC simulation
        V1 = DCVoltageSource(voltage=1.0, id='V1')
        R1 = Resistor(resistance=1000)
        L1 = Inductor(inductance=1e-3)
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1, 2])
        circuit.add(L1,[2, 0])
        voltages, currents = solve_dc(circuit)
        # The voltage at node 1 should be 1 volt, as the inductor should not affect the DC voltage.
        assert(within(np.abs(voltages[1]), 1.0, 0.1))
        # No phase shift for DC voltage, so the imaginary part should be close to zero.
        assert(np.imag(voltages[1]) < 1e-6)
        # The voltage at node 2 should be 0 volts, as the inductor should be a short for DC current.
        assert(np.abs(voltages[2]) < 1e-6)
        # Current should be 1mA, as the inductor should be a short for DC current.
        assert(within(np.abs(currents[R1.id]), 0.001, 0.1))

    def test_26(self):
        # R and C in series with 1 volt DC source
#        V1 = SinusoidalVoltageSource(amplitude=1.0, ac_source=True, id='V1')
        V1 = DCVoltageSource(voltage=1.0, id='V1')
        R1 = Resistor(resistance=1000)
        C1 = Capacitor(capacitance=1e-6)
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1, 2])
        circuit.add(C1,[2, 0])
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        # Voltage at top of resistor should be 1 volt, as the capacitor is an open the DC voltage.
        assert(within(np.abs(voltages[1]),1,0.1))
        # Voltage at top of capacitor should be 1 volts, as the capacitor is an open the DC voltage.
        assert(within(np.abs(voltages[2]),1,0.1))
        # Phase angle at top of resistor should be 0, as the capacitor is an open the DC voltage.
        assert(np.imag(voltages[1]) < 1e-6)
        # Phase angle at top of capacitor should be 0, as the capacitor is an open the DC voltage.
        assert(np.imag(voltages[2]) < 1e-6)
        # Current should be 0, as the capacitor is an open the DC voltage.
        assert(np.abs(currents[R1.id]) < 1e-6)

    def test_27(self):
        # Is a zero volt voltage source equivalent to a short?
        V1 = DCVoltageSource(voltage=1.0)
        V2 = DCVoltageSource(voltage=0.0)
        R1 = Resistor(resistance=1000)
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(V2,[1,2])
        circuit.add(R1,[2,0])
        voltages, currents = solve_dc(circuit)
        assert(within(np.abs(voltages[2]), 1.0, 0.1))
        assert(within(np.abs(currents[R1.id]), 0.001, 0.1))
        assert(within(np.abs(currents[V2.id]), 0.001, 0.1))

    def test_28(self):
        # Test a wire with zero resistance, should be a short circuit
        V1 = DCVoltageSource(voltage=1.0)
        R1 = Resistor(resistance=1e3)
        W1 = Wire(id='W1')
        circuit=Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1, 2])
        circuit.add(W1,[2, 0])
        voltages, currents = solve_dc(circuit)
        assert(within(np.abs(voltages[1]), 1.0, 0.1))
        assert(within(np.abs(currents[R1.id]), 0.001, 0.1))
        assert(np.abs(voltages[2]) < 1e-6)
        assert(within(np.abs(currents[W1.id]), 0.001, 0.1))
        assert(within(np.abs(currents[W1]), 0.001, 0.1))

    def test_29(self):
        # Test a wire with zero resistance, should be a short circuit
        V1 = DCVoltageSource(voltage=1.0)
        R1 = Resistor(resistance=1e3)
        W1 = Wire(id='W1')
        circuit=Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1, 2])
        circuit.add(W1,[2, 0])
        voltages, currents = solve_dc(circuit)
        print_currents_voltages(circuit, voltages, currents)
        assert(within(np.abs(voltages[1]), 1.0, 0.1))
        assert(within(np.abs(currents[R1.id]), 0.001, 0.1))
        assert(np.abs(voltages[2]) < 1e-6)
        assert(within(np.abs(currents[W1.id]), 0.001, 0.1))
        assert(within(np.abs(currents[W1]), 0.001, 0.1))

    def test_30(self):
        # Test a VCCS
        V1 = DCVoltageSource(voltage=1.0)
        VCCS1 = VCCS(gm=2.5, id='VCCS1')
        R1 = Resistor(resistance=1e3)
        R2 = Resistor(resistance=1e3)
        R3 = Resistor(resistance=1e3)
        circuit=Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,0])
        circuit.add(R2,[1,2])
        circuit.add(R3,[3,0])
        circuit.add(VCCS1,[2,3,1,0]) # order is (out-, out+, in-, in+)
        _, currents = solve_dc(circuit)
        assert(within(np.abs(currents[R3]), 2.5, 0.1))

    def test_31(self):
        # Test a VCCS
        V1 = DCVoltageSource(voltage=1.0)
        VCCS1 = VCCS(gm=2.5, id='VCCS1')
        R1 = Resistor(resistance=1e3)
        R2 = Resistor(resistance=1e3)
        R3 = Resistor(resistance=1e3)
        circuit=Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R2,[1,2])
        circuit.add(R1,[2,0])
        circuit.add(R3,[3,0])
        circuit.add(VCCS1,[2,3,2,0])
        _, currents = solve_dc(circuit)
        assert(within(np.abs(currents[R3]), 0.001, 0.1))

    def test_32(self):
        # Test a VCCS
        I1 = DCCurrentSource(current=1, id='I1')
        VCCS1 = VCCS(gm=2.5, id='VCCS1')
        R1 = Resistor(resistance=1e3)
        R2 = Resistor(resistance=1e3)
        R3 = Resistor(resistance=1e3)
        circuit=Circuit()
        circuit.add(I1,[0,1])
        circuit.add(R1,[1,0])
        circuit.add(R2,[1,2])
        circuit.add(R3,[2,0])
        circuit.add(VCCS1,[2,0,0,1])
        _, currents = solve_dc(circuit)
        print('AC_test_10, currents[R3]=',currents[R3])
        assert(within(np.abs(currents[R3]), 0.9984, 0.001))
        print('AC_test_10, currents[VCCS1]=',currents[VCCS1])
        assert(within(np.abs(currents[VCCS1]), 1.9976, 0.001))
        assert(within(np.abs(currents[VCCS1.id]), 1.9976, 0.001))

    def test_33(self):
        # test if we can get the current through a component by using the component reference instead of the component id
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,0])
        result = solve_dc(circuit)
        IR1_1 = result[1][R1.id]
        IR1_2 = result[1][R1]
        assert(IR1_1 == IR1_2)


class Test_AC:

    def test_1(self):
        # Two 1 volt voltages sources, in counter phase, over a 1kOhm resistor.
        # Current through R1 should be 0
        V1 = SinusoidalVoltageSource(amplitude=1, ac_source=True, phase=0, id='V1')
        V2 = SinusoidalVoltageSource(amplitude=1, ac_source=True, phase=np.pi, id='V2')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(V2,[1,2])
        circuit.add(R1,[2,0])
        _, currents = solve_ac(circuit,freq=1e3)
        IR1 = np.abs(currents[R1])
        assert(IR1 < 1e-6)

    def test_2(self):
        # Two 1 volt voltages sources, in phase, over a 1kOhm resistor.
        # Current through R1 should be 2mA
        V1 = SinusoidalVoltageSource(amplitude=1, ac_source=True, phase=0, id='V1')
        V2 = SinusoidalVoltageSource(amplitude=1, ac_source=True, phase=0, id='V2')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(V2,[1,2])
        circuit.add(R1,[2,0])
        _, currents = solve_ac(circuit,freq=1e3)
        IR1 = np.abs(currents[R1])
        assert(within(IR1, 0.002, 0.1))

    def test_3(self):
        # Test if a circuit without AC source in an AC simulation will be trapped.
        V1 = DCVoltageSource(voltage=1.0)
        R1 = Resistor(resistance=1e3)
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1,0])
        with pytest.raises(TopologyError):
            voltages, currents = solve_ac(circuit,freq=1e3)

    def test_4(self):
        # Test a diode in AC simulation
        V1 = SinusoidalVoltageSource(amplitude=.5, ac_source=True, id='V1')
        D1 = Diode(id='D1')
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(D1,[1,0])
        voltages, currents = solve_ac(circuit,freq=1e3)
        IV1 = currents[V1]
        ID1 = currents[D1]
        print_currents_voltages(circuit, voltages, currents)
        # current through the diode should be equal
        # to the current through the voltage source,
        # as they are in series.
        assert IV1 == ID1
#        assert (within(IV1, ID1, 0.1))

    def test_5(self):
        # Test a diode in AC simulation with a DC offset
        ampl = .5
        V1 = SinusoidalVoltageSource(amplitude=ampl, dc=0.5, phase=0.5, ac_source=True, id='V1')
        D1 = Diode(id='D1')
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(D1,[1,0])
        voltages, currents = solve_ac(circuit,freq=1e3)
        V_D1 = voltages[1]
        I_V1 = currents[V1]
        I_D1 = currents[D1]
        print_currents_voltages(circuit, voltages, currents)
        # current through the diode should be equal
        # to the current through the voltage source,
        # as they are in series.
        assert I_V1 == I_D1
        assert np.angle(V_D1) == np.angle(I_D1)

class Test_transient:

    def test_1(self):
        # 1 volt over 1k resistor.
        # Test node 1 voltage 1 volt with transient analysis
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(R1,[1, 0])
        time, nodes, comps = solve_transient(circuit,t_stop=1, dt=1e-3)
        VR1 = nodes[1][0]
        assert(within(VR1,1,0.1))

    def tt_2(self):
        # RC network, test if it follows the timeconstant formula
        r = 1000
        c = 1e-6
        t_rc = r * c
        v1 = 10.0
        V1 = DCVoltageSource(voltage=v1)
        R1 = Resistor(resistance=r)
        C1 = Capacitor(capacitance=c, initial_voltage=0.0)
        circuit = Circuit()
        circuit.add(V1,[0,1])
        circuit.add(R1,[1, 2])
        circuit.add(C1,[2, 0])
        time, nodes, comps = solve_transient(circuit,t_stop=0.01, dt=1e-4)
        v = np.abs(nodes[2])
        # The voltage across the capacitor should be v*(1-exp(-t/t_rc))
        v_expected = v1 * (1 - np.exp(-time/t_rc))
        # Check that the voltage is within 10% of the expected value
        # Do not test the first ten samples,as it may have to settle in.
        for ve, va in zip(v_expected[10:], v[10:]):
            assert(within(va, ve, 10))

    def test_3(self):
        # 1 volt over 1k resistor.
        # Test R1 1mA current with transient analysis
        circuit = Circuit()
        V1 = DCVoltageSource(voltage=1, id='V1')
        R1 = Resistor(resistance=1e3, id='R1')
        circuit.add(V1,[0,1])
        circuit.add(R1,[1, 0])
        time, nodes, comps = solve_transient(circuit,t_stop=1, dt=1e-3)
        IR1 = comps[R1.id][0]
        assert(within(IR1,0.001,0.1))


# Test_Circuit().test_4()
# Test_transient().test_1()
Test_AC().test_5()
# Test_DC().test_11()
# Test_DC().test_12()
# Test_DC().test_13()
# Test_DC().test_14()
#Test_DC().test_20()
# Test_AC().test_2()
