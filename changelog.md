## [2.0.1] - 2026-05-28

- implementation of a new diode soft limiter in diode.py. This work has been
  done for issue #1. The new diode soft limiter is enabled by default. To
  disable it, set _simple_limiter to True. Its behaviour (the moment at
  which the limiter kicks in) can be influenced by setting DIODE_LIMITER_NVT
  which defaults to 1. If the diode voltage as advised by solution of the
  previous MNA solver iteration is higher than DIODE_LIMITER_NVT * n * Vt,
  the soft limiter kicks in. Lower values of DIODE_LIMITER_NVT make the
  limiter more agressive, higher values make it more relaxed. This value
  may need to be adjusted per different Circuit. To make it fully
  automatic makes this project move into advanced territory and thus
  should be done in impulsox-mna instead of this project.
- make Opamp less hard for the solver. It is less stiff now.
- introduce realify, imagify and magify in pivot.py. These functions return
  the real parts, imaginary parts and magnitude respectively of simulation results
- refactor i_pivot and v_pivot functions in pivot.py. They relegate
  work to _pivot_generic() now.
- new example 'diode_soft_limit_test.py' which tests the diode soft limiter
- some tests have been improved

## [2.0.0] - 2026-05-21

- interface for Solver_ACDC.__init__() simplified
- stamping for Inductor and MutualInductance rewritten. Now these are all stamped by a single InductorGroup, which stamps them all at once.
- added example transformer.py
- return values of Component.before_add() have changed. Now it only returns a single bool, which tells if the component should be added to the circuit or not.
- Component now implement returns_current() and stamps(), which tell if the component returns a current value after solving the circuit, and if the component stamps itself in the circuit. An Inductor does not stamp itself into the admittance matrix (so returns False), although it is stamped into the admittance matrix. This is done by an InductorGroupo however (which itself is not stamped into the matrix). The preparation is only done once for an entire solve or series of solves for the current Circuit.
- Solve_ACDC.solve_mna() now has a preparation stage (prepare_for_solving()) before the actual solving is done. This allows for helper objects to be created before the actual solving starts. Currently a InductorGroup is introduced in this preparation stage, which stamps all Inductors and MutualInductances, which do not stamp themselves anymore.
- Before solving, the Components are asked whether they stamp themselves into the admittance matrix by calling Component.stamps(). This should return True if the component stamps itself.
- Before solving, the Components are asked whether they return a current after the solve by calling Component.returns_current(). This should return True if the Component returns a current.
- two pytest tests added: TestAC.test_6() and TestAC.test_7() which test a transformer with coupling of 1 and dots opoosite (test_7) or not opposite (test_6).
- new testscript named test_examples.py tests all example scripts in the .examples folder.
- Circuit has a new attribute 'components_not_added' which contains all not-added components (mainly used for compound components such as BJT's).
- Circuit.component has changed from a dict[str:Component] to a list[Component]. The lookup from comp.id to Component was never used and a list is easier. Also renamed from component to components. Similar for Solver_ACDC.component.
- finished stamping docs




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


