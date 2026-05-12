## [1.2.0] -



## [1.1.0] - 2026-05-10

- SinusoidalVoltageSOurce now can use ampitudes other than 1 for AC analysis
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


