# References

1. Ali Hajimiri (Caltech), https://youtu.be/E6SWCh33L7U?list=PLc7Gz02Znph_HU1I9STgC4Nv0aG_jdb8Z (for resistor)
2. Ali Hajimiri (Caltech), https://youtu.be/QQCYJnmbXYw?list=PLc7Gz02Znph_HU1I9STgC4Nv0aG_jdb8Z (for VCCS)
3. Ali Hajimiri (Caltech), https://youtu.be/DJcvNUkzWmQ?list=PLc7Gz02Znph_HU1I9STgC4Nv0aG_jdb8Z (for voltage source)

# Nodal Analysis

Nodal analysis of an electric circuit is done by creating a set of linear equations describing the currents entering any node (except the ground node) and solving this system of equations. This is a linear algebra problem for which fast ways to solve them exist.

If components do not have a linear voltage-current relationship (such as diodes) the component will have to be linearized around an operating point. Then the system will be solved in the linear way. If the convergence criteria are not met, the device will have to be repeatedly linearized around a new operating point until convergence.

For a circuit with n nodes:

1. Select reference node (a.k.a. ground)
2. Define voltage (v<sub>1</sub>, v<sub>2</sub>, ..., v<sub>n</sub>) wrt ground
3. Apply KCL to all nodes, current expressed in terms of node voltages
4. Solve the resulting linear algebra problem

For every node the KCL equation says $\sum{i} = 0$, all currents leaving (or entering) the node add up to $0$. Here $i$ are the currents between the nodes, and are expressed in terms of admittances and voltages.

For every node $i$ the KCL equation is:
$$
\sum_j  Y_{ij}\left( v_i-v_j\right)-I_i= 0
$$
where

- $j$ are all the nodes connected to $i$
- $I_i$ is the sum of currents leaving node $i$ produced by independent current sources
- $Y_{ij}$ is the admittance of the circuit element between node $i$ and node $j$
- $v_i$ and $v_j$ are the voltages of nodes $i$ and $j$ respectively.

Express these KCL equations in terms of node voltages. This gives a set of linear equations which can be expressed in matrix form as

$$
\mathbf{Y} \cdot \vec{v}=\vec{I}
$$

$$
\left[
\begin{array}{cccc}
   Y_{11} & Y_{12} & \cdots & Y_{1n} \\
   Y_{21} & Y_{22} & \cdots & Y_{2n} \\

   \vdots & \; & \ddots & \vdots \\
   Y_{n1} & \cdots & \cdots & Y_{nn}
   \end{array}
\right] \cdot
\left[
\begin{array}{c}
   v_1 \\
   v_2 \\
   \vdots \\
   v_n
   \end{array}
\right] =
\left[
\begin{array}{c}
   I_1 \\
   I_2 \\
   \vdots  \\
   I_n
   \end{array}
\right]
$$

$\mathbf{Y}$ is called the admittance matrix. $\vec{I}$ is the stimulus vector. This matrix equation can be solved for $\vec{v}$, which is a vector representing the node voltages. $\vec{v}$ is called the solution vector.

The matrix equation $\mathbf{Y} \cdot \vec{v}=\vec{I}$ can be solved using linear algebra methods. For this standard software packages are readily available.

Values in $\mathbf{Y}$ can have (frequency dependent) complex values for reactive components such as capacitors and inductors. Also values in $\vec{v}$ and $\vec{I}$ can have complex values. This way AC analysis is done.



# Modified Nodal Analysis

In MNA auxiliary equations (for voltage sources, inductors) diagonal entries are **not admittances**. They are whatever coefficient arises from the constitutive equation.

The MNA matrix equation is

$$
Ax=z
$$

where

$\mathbf{A}$ contains coefficients relating unknown variables,
$\vec{x}$ contains the unknown node voltages and auxiliary currents,
$\vec{z}$ contains independent excitations.
For dynamic components such as capacitors and inductors, the stamping differs between DC, AC, and transient analysis.

One nuance worth mentioning: an independent voltage source also modifies the matrix because it introduces an additional equation and unknown current,
but its value still appears in the RHS vector $\vec{z}$.

# Conventions

Currents leaving a node are taken as positive.

Independent sources contribute to the RHS vector.

Dependent sources contribute coefficients to the system matrix because their values depend on circuit unknowns.

# Frequency

In AC analysis the (complex) frequency is defined as $s=j\omega=2j\pi f$ with $f$ the frequency in Hz.


# Linear Components

## Resistor

A resistor $R_{ij}$ between nodes $i$ and $j$ stamps the admittance matrix $\mathbf{Y}$ as

$$
\left[
\begin{array}{c c c c c c}
   & & i & & j \\
    & \cdots & \cdots & \cdots & \cdots & \cdots\\
   i &\cdots & +G_{ij} & \cdots & -G_{ij} & \cdots\\
    & \cdots & \cdots & \cdots & \cdots & \cdots\\
   j & \cdots & -G_{ij} & \cdots & +G_{ij} & \cdots\\
   & \cdots & \cdots & \cdots & \cdots & \cdots\\
   \end{array}
\right]
$$

where $G_{ij}=1 / R_{ij}$.

See [1].


## Capacitor

A capacitor $C_{ij}$ between nodes $i$ and $j$ stamps the admittance matrix $\mathbf{Y}$ as

$$
\left[
\begin{array}{c c c c c c}
   & & i & & j \\
    & \cdots & \cdots & \cdots & \cdots & \cdots\\
   i &\cdots & +G_{ij} & \cdots & -G_{ij} & \cdots\\
    & \cdots & \cdots & \cdots & \cdots & \cdots\\
   j & \cdots & -G_{ij} & \cdots & +G_{ij} & \cdots\\
   & \cdots & \cdots & \cdots & \cdots & \cdots\\
   \end{array}
\right]
$$

where $G_{ij}=sC_{ij}$.


## Inductor

### Admittance formulation (AC only)

A very simple way which works for AC analysis (neither DC, nor transient) is the following.

An inductor $L_{ij}$ between nodes $i$ and $j$ stamps the admittance matrix $\mathbf{Y}$ as

$$
\Delta \mathbf{Y} =
\left[
\begin{array}{c c c c c c}
   & & i & & j \\
    & \cdots & \cdots & \cdots & \cdots & \cdots\\
   i &\cdots & +G_{ij} & \cdots & -G_{ij} & \cdots\\
    & \cdots & \cdots & \cdots & \cdots & \cdots\\
   j & \cdots & -G_{ij} & \cdots & +G_{ij} & \cdots\\
   & \cdots & \cdots & \cdots & \cdots & \cdots\\
   \end{array}
\right]
$$

where $G_{ij}=1/sL_{ij}$.

It does not work for DC because at DC $s=0$ causing numerical problems. A special case would need to be constructed for DC with $G=\mathrm{very large}$.

For transient analysis we need an entirely different way, similar to capacitors in transient analysis.

### Standard MNA formulation

For an inductor L between nodes $i$ and $j$, positive current flowing from node $i$ to node $j$

$$
v_L(s)=sLi_L
$$

which can be rewritten as

$$
v_L(s) = v_i - v_j=sLi_L
$$

We define an extra unknown, the inductor current $i_L$ so the unknown vector $\vec{x}$ becomes

$$
\vec{z}=\left[
\begin{array}{c}
   v_1 \\
   v_2 \\
   \vdots \\
   i_L
   \end{array}
\right]
$$

Then the KCL contributions are:

* $+i_L$ for node $i$
* $-i_L$ for node $j$

This produces
* $Y[i,i_L]+=1$
* $Y[j,i_L]-=1$

where $\mathbf{Y}$ now is the system matrix. The system matrix $\mathbf{Y}$ extends the nodal admittance matrix with auxiliary rows and columns for additional current and constraint equations.

Now we enforce $v_i - v_j - sLi_L = 0$.

This becomes an extra row in the MNA:

$(+1)v_i + (-1)v_j - sL(i_L) = 0$

which stamps as

$$
Y[i_L,i] += 1 \\
Y[i_L,j] -= 1 \\
Y[i_L,i_L] -= sL
$$

The full stamping becomes:

$$
\Delta\mathbf{Y} =
\left[
\begin{array}{c c c c c c | c}
   & & i & j &  &  & i_L\\
    & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   i &\cdots & \cdots & \cdots & \cdots & \cdots & +1 \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots & -1 \\
    & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
    & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   \hline
   i_L & \cdots & +1 & -1 & \cdots & \cdots & -sL \\
   \end{array}
\right]
$$

### Mutual Inductance
#### General

For two coupled inductors:

$$v_1 = L_1 \frac{di_1}{dt} + M \frac{di_2}{dt}$$
$$v_2 = L_2 \frac{di_2}{dt} + M \frac{di_1}{dt}$$

When we write

$$i = \begin{bmatrix} i_1 \\ i_2 \end{bmatrix}, \quad
v = \begin{bmatrix} v_1 \\ v_2 \end{bmatrix}$$
Then:

$$v =
\begin{bmatrix}
L_1 & M \\
M & L_2
\end{bmatrix}
\frac{di}{dt}$$

Call this matrix:

$$\mathbf{L} =
\begin{bmatrix}
L_1 & M \\
M & L_2
\end{bmatrix}$$

The matrix $\mathbf{L}$ is the inductance matrix. A mutual inductance is represented by a matrix-values inductance. The mutual inductance between two inductors $L_1$ and $L_2$ = $M_{12}=k_{12}\sqrt{L_1L_2}$, where $k$ is the coupling factor between the two inductors, $\left| k_{12}\right|\le 1$. If the winding orientation of the two coils is opposite, $M$ is negative.

When all coupled inductors are regarded as a single multiport element, the equations remain structurally identical to the single-inductor case.

A coupled inductor system is simply:

$$v = \mathbf{L} \frac{di}{dt}$$

where $\mathbf{L}$ is no longer scalar.

$\mathbf{L}$ can be expanded to any size for any number of coupled inductors. For non-coupled inductors $i$ and $j$ the mutual inductance $M_{ij}=0$. For a system with three inductors

$$\mathbf{L} =
\begin{bmatrix}
L_1 & M_{12} & M_{13} \\
M_{21} & L_2 & M_{23} \\
M_{31} & M_{32} & L_3
\end{bmatrix}$$

For only a single inductor in the circuit $\mathbf{L}$ reduces to
$$
\mathbf{L} = L
$$

Every inductor augments the admittance matrix with its own row. This row defines the current-voltage relation over this single inductor. The rows associated with the auxiliary inductor currents are coupled through the inductance matrix L.

#### Transient simulation

Using backward Euler, you get:

$$\frac{di}{dt} \approx \frac{i^{n} - i^{n-1}}{\Delta t}$$

So:

$$v^{n} = \mathbf{L} \cdot \frac{i^{n} - i^{n-1}}{\Delta t}$$

Rearrange:

$$v^{n} = \underbrace{\frac{\mathbf{L}}{\Delta t}}_{\mathbf{Z}_{eq}} i^{(n)}

- \underbrace{\frac{\mathbf{L}}{\Delta t}}_{\mathbf{Z}_{eq}} i^{(n-1)}$$

So the equivalent is:

* A **matrix impedance**
  $$\mathbf{Z}_{eq} = \frac{\mathbf{L}}{\Delta t}$$

* parallel with a **history voltage source**
  $$v_{hist} = \frac{\mathbf{L}}{\Delta t} i^{(n-1)}$$

The matrix impedance $\mathbf{Z}_{eq}$ stamps the matrix $\mathbf{Y}$ as:
$$
\Delta \mathbf{Y} =
\left[
\begin{array}{c c c c c : c c}
   & i & j & p & q & i_{L_1} & i_{L_2} \\
    i & \cdots & \cdots & \cdots & \cdots & +1 & \cdots \\
    j & \cdots & \cdots & \cdots & \cdots & -1 & \cdots \\
    p & \cdots & \cdots & \cdots & \cdots & \cdots & +1 \\
    q & \cdots & \cdots & \cdots & \cdots & \cdots & -1 \\
   \hdashline
    i_{L_1} & +1 & -1 & \cdots & \cdots & -L_1/{\Delta t} & -M_{12}/{\Delta t} \\
    i_{L_2} & \cdots & \cdots & +1 & -1 & -M_{21}/{\Delta t} & -L_2/{\Delta t} \\
   \end{array}
\right]
$$
where $L_1$ is the inductor between nodes $i$ and $j$, and $L_2$ the inductor between $p$ and $q$. Note that $M_{12}=M_{21}$.

The history voltage source stamps in the RHS vector $\vec{z}$ as:
$$
\Delta \vec{z} =
\left[
\begin{array}{c}
\cdots \\
\cdots \\
\cdots \\
\cdots \\
\hdashline
\frac{i_{L_1}^{(n-1)}L_1 + i_{L_2}^{(n-1)}M_{21}}{\Delta t} \\
\frac{i_{L_1}^{(n-1)}M_{12} + i_{L_2}^{(n-1)}L_2}{\Delta t}\\
\end{array}
\right]
$$

The rows $i_{L_1}$ and $i_{L_2}$ in $\Delta \mathbf{Y}$ and $\Delta \vec{z}$ encode the equation
$$
\begin{bmatrix}
v_1 \\
v_2
\end{bmatrix}
-\mathbf{Z}_{eq}
\begin{bmatrix}
i_1 \\
i_2
\end{bmatrix}^{(n)}
= -\mathbf{Z}_{eq}
\begin{bmatrix}
i_1 \\
i_2
\end{bmatrix}^{(n-1)}
$$
The history term contributes negatively to the RHS vector because it is moved to the right-hand side of the constitutive equation.

This stamping is similar to single inductor stamping as described in 'Standard MNA formulation', generalized to matrix form.


#### AC simulation

For AC simulation we have
$$
\mathbf{Z} = s\mathbf{L}
$$

The matrix $\mathbf{Y}$ is stamped as follows:
$$
\Delta \mathbf{Y} =
\left[
\begin{array}{c c c c c : c c}
   & i & j & p & q & i_{L_1} & i_{L_2} \\
    i & \cdots & \cdots & \cdots & \cdots & +1 & \cdots \\
    j & \cdots & \cdots & \cdots & \cdots & -1 & \cdots \\
    p & \cdots & \cdots & \cdots & \cdots & \cdots & +1 \\
    q & \cdots & \cdots & \cdots & \cdots & \cdots & -1 \\
   \hdashline
    i_{L_1} & +1 & -1 & \cdots & \cdots & -sL_1 & -sM_{12} \\
    i_{L_2} & \cdots & \cdots & +1 & -1 & -sM_{21} & -sL_2 \\
   \end{array}
\right]
$$

The source vector $\vec{z}$ is stamped as

$$
\Delta \vec{z} =
\left[
\begin{array}{c}
\cdots \\
\cdots \\
\cdots \\
\cdots \\
\hdashline
\cdots \\
\cdots \\
\end{array}
\right]
$$

ie, it is not stamped.

This stamping encodes the equation
$$
\vec{v}-s\mathbf{L}\vec{i}=0
$$


#### DC simulation
For DC simulation the matrix $\mathbf{Y}$ is stamped as follows:
$$
\Delta \mathbf{Y} =
\left[
\begin{array}{c c c c c : c c}
   & i & j & p & q & i_{L_1} & i_{L_2} \\
    i & \cdots & \cdots & \cdots & \cdots & +1 & \cdots \\
    j & \cdots & \cdots & \cdots & \cdots & -1 & \cdots \\
    p & \cdots & \cdots & \cdots & \cdots & \cdots & +1 \\
    q & \cdots & \cdots & \cdots & \cdots & \cdots & -1 \\
   \hdashline
    i_{L_1} & +1 & -1 & \cdots & \cdots & \cdots & \cdots \\
    i_{L_2} & \cdots & \cdots & +1 & -1 & \cdots & \cdots  \\
   \end{array}
\right]
$$

The source vector $\vec{z}$ is stamped as

$$
\Delta \vec{z} =
\left[
\begin{array}{c}
\cdots \\
\cdots \\
\cdots \\
\cdots \\
\hdashline
\cdots \\
\cdots \\
\end{array}
\right]
$$
This encodes the equation
$$
\vec{v}=0
$$
since at DC there is no voltage drop over an inductor, while the inductor currents remain unconstrained.


# Non-linear Components

## Diode

The non-linear diode is linearized using the Newton-Raphson method.

The diode equation is

$$
i_D = I_s(\mathrm{e}^{v_D/V_T}-1)
$$

We will approach the value for $i_D$ by iterating over step $k$ around the current estimate $v_D^{(k)}$. We approximate the diode current with a first-order Taylor expansion:

$$
i_D^{(k+1)}
\approx
i_D^{(k)}
+
\left.\frac{di_D}{dv_D}\right|_{v_D^{(k)}}
\left(v_D^{(k+1)} - v_D^{(k)}\right)
$$

or equivalently:

$$
i_D
\approx
g_D^{(k)} v_D + I_{\mathrm{eq}}^{(k)}
$$

with

$$
I_{\mathrm{eq}}^{(k)}
= i_D^{(k)} - g_D^{(k)}v_D^{(k)}
$$

where

$$
g_D^{(k)} = \frac{\delta i_D^{(k)}}{\delta v_D} = \frac{I_s}{V_T}\mathrm{e}^{v_D^{(k)}/V_T}
$$

This makes the diode a parallel combination of a current source $i_D^{(k)}$ and a conductance $g_D^{(k)}=\frac{I_s}{V_T}\mathrm{e}^{v_D^{(k)}}/V_T$. For a diode between nodes $i$ and $j$, the complete stamping thus becomes:

$$
\Delta\mathbf{Y} = \left[
\begin{array}{c c c c c c}
   & & i & j & p & q \\
    & \cdots & \cdots & \cdots & \cdots & \cdots \\
   i &\cdots & +g_D^{(k)} & -g_D^{(k)} & \cdots & \cdots \\
   j & \cdots & -g_D^{(k)} & +g_D^{(k)} & \cdots & \cdots \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots \\
   \end{array}
\right]
$$

and

$$
\Delta\vec{z} = \left[
\begin{array}{ccc}
   & \vdots \\
   i: & -i_D^{(k)} \\
   & \vdots  \\
   j: & +i_D^{(k)} \\
   & \vdots
   \end{array}
\right]
$$






# Independent Sources

## Voltage Source

A voltage source $V_{ij} = V_j-V_i$ produces an extra expression  in the matrix $\mathbf{Y}$, which augments the nodal system. The extra equation gives an extra row and extra column at index $a$ with the following entries:

The current $I_{ij}$ flowing from node $i$ through the voltage source to node $j$ is an extra $+1$ addition in the extra column for node $i$ and a $-1$ addition for node $j$ which will calculate the current $I_{ij}$ as an extra value $z_a$ in the solution vector $\vec{z}$. The auxiliary current variable is defined positive from node i to node j.

Stamping the voltage source will be as follows:

$$
\Delta \mathbf{Y} =
\left[
\begin{array}{c c c c c c | c}
   & & i & j & p & q & a\\
    & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   i &\cdots & \cdots & \cdots & \cdots & \cdots & +1 \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots & -1 \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   \hline
   a & \cdots & -1 & +1 & \cdots & \cdots & 0 \\
   \end{array}
\right]
$$

and the stamping in the RHS vector

$$
\Delta \vec{z} = \left[
\begin{array}{c}
   \cdots \\
   \cdots \\
   \cdots  \\
   \cdots  \\
   \cdots \\
   \hline
   V_{ij}
   \end{array}
\right]
$$

Row $a$ represents the equation $V_{ij}=V_j-V_i$. Column $a$ calculates the current $I_{ij}$.


## Current Source

A current source $I_{ij}$ between nodes $i$ and $j$ with current flowing from $i$ to $j$ stamps the RHS vector $\vec{z}$ as

$$
\Delta \vec{z} = \left[
\begin{array}{ccc}
   & \vdots \\
   i: & -I_{ij} \\
   & \vdots  \\
   j: & +I_{ij} \\
   & \vdots
   \end{array}
\right]
$$


# Dependent Sources

## CCVS

### Measuring current through a resistor or capacitor

The voltage between nodes $i$ and $j$ is controlled by the current $i_c$ through the component $c$ between nodes $p$ and $q$. The gain factor is $R_m$.

$$\begin{align}
v_{ccvs}=v_j-v_i &= R_m \cdot i_c \\
&= R_m \cdot (v_q-v_p) \cdot G_{pq}
\end{align}$$

$G_{pq}$ is the admittance of the resistor or capacitor.

So the equation for the voltage constraint is:
$$
\begin{align}
v_j-v_i-G_{pq}R_mv_q+G_{pq}R_mv_p=0
\end{align}
$$

This stamps the admittance matrix as:

$$
\Delta \mathbf{Y} =
\left[
\begin{array}{c : c c c c c c}
\; & j & \; & i & p & q & i_{ccvs} \\ \\
   \hdashline \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots & -1 \\
   \; & \cdots &\cdots & \cdots & \cdots & \cdots & \cdots \\
   i & \cdots & \cdots & \cdots & \cdots & \cdots & +1 \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots  \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   v_{ccvs} & +1 & \cdots & -1 & +G_{pq}R_m & -G_{pq}R_m & 0 \\
   \end{array}
\right]
\cdot
\left[
\begin{array}{c}
   v_1 \\
   v_2 \\
   \vdots \\
   v_n \\
   i_{ccvs}
\end{array}
\right] =
\left[
\begin{array}{c}
   i_1 \\
   i_2 \\
   \vdots  \\
   i_n \\
   0
   \end{array}
\right]
$$

$G_{pq}R_m$ is dimensionless.



### Measuring current through a zero-volt voltage source

With a zero-volt voltage source the process is as follows. The zero-volt voltage source $v_0$ is connected between nodes $p$ and $q$. The node equation is

$$
v_0 = v_q-v_p = 0
$$

This equation for the zero-volt voltage source is stamped in the matrix.

The current controlled voltage $v_{ccvs}=R_m \cdot i_{v_0}$, where $i_{v_0}$ is the controlling current through the zero-volt voltage source. The voltage $v_{ccvs}$ is between nodes $i$ and $j$, so $v_{ccvs} = v_j-v_i$, which makes the equation

$$
v_j-v_i-R_m \cdot i_{v_0}=0
$$

This stamps the matrix as follows:

$$
\Delta \mathbf{Y} =
\left[
\begin{array}{c : c c c c c c c}
\; & j & \; & i & p & q & i_{v_0} & i_{ccvs} \\ \\
\hdashline \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots & -1 \\
   \; & \cdots &\cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   i & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots & +1 \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   v_0 & \cdots & \cdots & \cdots & -1 & +1 & \cdots & \cdots \\
   v_{ccvs} & +1 & \cdots & -1 & \cdots & \cdots & -R_m & \cdots \\
   \end{array}
\right] \cdot
\left[
\begin{array}{c}
   v_j \\
   \vdots \\
   v_i \\
   v_p \\
   v_q \\
   i_{v_{0}} \\
   i_{ccvs}
   \end{array}
\right] =
\left[
\begin{array}{c}
   0 \\
   0 \\
   0 \\
   0 \\
   0 \\
   0 \\
   0
   \end{array}
\right]$$


## VCVS

The controlling voltages are at nodes $p$ and $q$. The gain factor is $A$.

$$
v_j-v_i=A \cdot (v_q-v_p)
$$

$$
v_j-v_i-Av_q+Av_p=0
$$

VCVS stamping:
$$
\Delta \mathbf{Y} =
\left[
\begin{array}{c : c c c c c c}
\; & j & \; & i & p & q & i_{vcvs} \\ \\
\hdashline \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots & -1 \\
   \; & \cdots &\cdots & \cdots & \cdots & \cdots & \cdots \\
   i & \cdots & \cdots & \cdots & \cdots & \cdots & +1 \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots  \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   v_{vcvs} & +1 & \cdots & -1 & +A & -A & 0 \\
   \end{array}
\right] \cdot
\left[
\begin{array}{c}
   v_1 \\
   v_2 \\
   \vdots \\
   v_n \\
   i_{vcvs}
   \end{array}
\right] =
\left[
\begin{array}{c}
   i_1 \\
   i_2 \\
   \vdots  \\
   i_n \\
   0
   \end{array}
\right]$$



## CCCS

The current through the CCCS is controlled by the current over a resistor, capacitor or zero-volt voltage source.

### CCCS with current measured by resistor or capacitor

Note that a CCCS controlled by a resistor or capacitor may cause ill-defined (singular) matrices because the CCCS may cancel conductances if the CCCS is connected to a node to which a controlling component is also connected.

Controlled by a resistor or capacitor, the current $I_{ij}=A \cdot I_x$, where $I_x$ is the controlling current, and $I_{ij}$ the current from node $i$ to node $j$  being controlled. The controlling current $I_x=Y_{pq} \cdot (V_p-V_q)$, where $p$ and $q$ are the nodes to which the resistor or capacitor is connected to.

$$
\Delta \mathbf{Y} =
\begin{align}
I_{ij} &= A \cdot I_x \\
& =A \cdot Y_{pq} \cdot (V_p-V_q) \\
&= AY_{pq}V_p - AY_{pq}V_q
\end{align}
$$
- extra current for node $i$ (outgoing, dependent current source): $-I_{ij} = AY_{pq}(V_p-V_q)$
- extra current for node $j$ (incoming, dependent current source): $+I_{ij} = AY_{pq}(V_q-V_p)$

This stamps th matrix as follows:
$$\left[
\begin{array}{c : c c c c c}
\; & j & \; & i & p & q \\ \\
\hdashline \\
   j & \cdots & \cdots & \cdots &  -AY_{pq} & +AY_{pq}  \\
   \; & \cdots &\cdots & \cdots & \cdots & \cdots  \\
   i & \cdots & \cdots & \cdots & +AY_{pq} & -AY_{pq}  \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots  \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots  \\
   \end{array}
\right] \cdot
\left[
\begin{array}{c}
   v_1 \\
   v_2 \\
   \vdots \\
   v_n \\
   \end{array}
\right] =
\left[
\begin{array}{c}
   i_1 \\
   i_2 \\
   \vdots  \\
   i_n
   \end{array}
\right]
$$

### CCCS with current measured by zero-volt voltage source


$I_{ij}=A \cdot I_{V_0}$

- extra current for node $i$: $A \cdot I_{V_0}$
- extra current for node $j$: $-A \cdot I_{V_0}$

$$
\left[
\begin{array}{c : c c c c c c}
\; & j & \; & i & p & q & i_{v_0} \\ \\
\hdashline \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots & -A \\
   \; & \cdots &\cdots & \cdots & \cdots & \cdots & \cdots \\
   i & \cdots & \cdots & \cdots & \cdots & \cdots & A \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   v_0 & \cdots & \cdots & \cdots & -1 & +1 & \cdots \\
   \end{array}
\right] \cdot
\left[
\begin{array}{c}
   v_1 \\
   v_2 \\
   \vdots \\
\vdots \\
   v_n \\
   I_{V_{0}} \\
   \end{array}
\right] =
\left[
\begin{array}{c}
   0 \\
   0 \\
   0 \\
   0 \\
   0 \\
   0
   \end{array}
\right]$$



## VCCS

A Voltage Controlled Current Source (VCCS) between nodes $i$ and $j$, producing a current flowing from $i$ to $j$ with magnitude $I_{ij}=G_m(V_p-V_q)$ where $V_p$ and $V_q$ are the controlling voltages, produces current

$G_m(V_p-V_q)$

out of node $i$ (negative) into node $j$ (positive). This causes the following additions to the matrix $\mathbf{Y}$:

$$
\Delta \mathbf{Y} =
\left[
\begin{array}{c c c c c c}
   & & i & j & p & q \\
    & \cdots & \cdots & \cdots & \cdots & \cdots \\
   i & \cdots & \cdots & \cdots & -G_m & +G_m \\
   j & \cdots & \cdots & \cdots & +G_m & -G_m \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots \\
   \end{array}
\right]
$$

See [2].


# Compound Components


