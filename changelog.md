## [2.0.0] -

- interface for Solver_ACDC.__init__() simplified
- stamping for Inductor and MutualInductance rewritten. Now these are all stamped by a single InductorGroup, which stamps them all at once.
- added example transformer.py
- return values of Component.before_add() have changed. Now it only returns a single bool, which tells if the component should be added to the circuit or not.
- Component now implement returns_current() and stamps(), which tell if the component returns a current value after solving the circuit, and if the component stamps itself in the circuit. An Inductor does not stamp itself into the admittance matrix (so returns False), although it is stamped into the admittance matrix. This is done by an InductorGroupo however (which itself is not stamped into the matrix). The preparation is only done once for an entire solve or series of solves for the current Circuit.
- Solve_ACDC.solve_mna() now has a preparation stage (prepare_for_solving()) before the actual solving is done. This allows for helper objects to be created before the actual solving starts. Currently a InductorGroup is introduced in this preparation stage, which stamps all Inductors and MutualInductances, which do not stamp themselves anymore.
- Before solving, the Components are asked whether they stamp themselves into the admittance matrix by calling Component.stamps(). This should return True if the component stamps itself.
- Before solving, the Components are asked whether they return a current after the solve by calling Component.returns_current(). This should return True if the Component returns a current.
- two pytest tests added: TestAC.test_6() and TestAC.test_7() which test a transformer with coupling of 1 and dots opoosite (test_7) or not opposite (test_6).



## [1.1.0] - 2026-05-10

- SinusoidalVoltageSource now can use ampitudes other than 1 for AC analysis
- solve_ac now performs operating point analysis prior to AC analysis
- solve_ac now accepts list of frequencies to perform AC analysis on. This effectively replaces ac_sweep
- optional parameters for sources are named now, unnamed not allowed anymore for clearer API design
- bug in diode current solved
- bug in ACVoltageSource and ACCurrentSource with DC offset in AC analysis solved
- stamping bug in R, C and D solved
- solve_ac operating point bug solved
- started docs for stamping
- CCCS stamping bug solved
- more parameter checks on API, can raise TopologyError, TypeError and ValueError now
- solver reads environment variable IMPULSO_DEBUG, if '1' prints debug info while solving


## [1.0] - 2026-05-05

Initial release


