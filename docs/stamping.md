$$
\left[
\begin{array}{c c c c c c}
   & & i & & j \\
    & \cdots & \cdots & \cdots & \cdots & \cdots \\
   i &\cdots & \cdots & \cdots & \cdots & \cdots \\
    & \cdots & \cdots & \cdots & \cdots & \cdots \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots \\
   & \cdots & \cdots & \cdots & \cdots & \cdots \\
   \end{array}
\right]
$$

$$
\left[
\begin{array}{c c c c c c}
   & & i & j & p & q \\
    & \cdots & \cdots & \cdots & \cdots & \cdots \\
   i &\cdots & \cdots & \cdots & \cdots & \cdots \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots \\
   \end{array}
\right]
$$

$$
\left[
\begin{array}{c c c c c c | c}
   & & i & j & p & q \\
    & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   i &\cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   \hline
    & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   \end{array}
\right]
$$



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
\begin{array}{ccc}
   Y_{11} & Y_{12} & \cdots & Y_{1n} \\
   Y_{21} & Y_{22} & \cdots & Y_{2n} \\

   \vdots & \; & \ddots & \vdots \\
   Y_{n1} & \cdots & \cdots & Y_{nn}
   \end{array}
\right] \cdot
\left[
\begin{array}{ccc}
   v_1 \\
   v_2 \\
   \vdots \\
   v_n
   \end{array}
\right] =
\left[
\begin{array}{ccc}
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

For some components with time varying behaviour stamping differs for AC and DC analysis

# Conventions

- dependent currents flowing out of a node are positive
- independent currents $I$ are positive into a node




# Linear Components

## Resistor

A resistor $R_{ij}$ between nodes {i} and {j} stamps the admittance matrix $\mathbf{Y}$ as

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

A capacitor $C_{ij}$ between nodes {i} and {j} stamps the admittance matrix $\mathbf{Y}$ as

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

An inductor $L_{ij}$ between nodes {i} and {j} stamps the admittance matrix $\mathbf{Y}$ as

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

where $G_{ij}=1/sL_{ij}$.



# Non-linear Components

## Diode


# Independent Sources

## Voltage Source

A voltage source $V_{ij} = V_j-V_i$ produces an extraexpression  in the matrix $\mathbf{Y}$, what makes the nodal analysis an augmented nodal analysis. The extra equation give an extra row and extra column at index $a$ with the following entries:

The current $I_{ij}$ flowing from node $i$ through the voltage source to node $j$ is an extra $+1$ addition in the extra column for node $i$ and a $-1$ addition for node $j$ which will calculate the current $I_{ij}$ as an extra value $z_a$ in the solution vector $\vec{z}$.
 Stamping the voltage source will be as such:

$$
\left[
\begin{array}{c c c c c c | c}
   & & i & j & p & q & a\\
    & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   i &\cdots & \cdots & \cdots & \cdots & \cdots & +1 \\
   j & \cdots & \cdots & \cdots & \cdots & \cdots & -1 \\
   p & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   q & \cdots & \cdots & \cdots & \cdots & \cdots & \cdots \\
   \hline
   a & \cdots & -1 & +1 & \cdots & \cdots & V_{ij} \\
   \end{array}
\right]
$$

The row represents the equation $V_{ij}=V_j-V_i$. The column $a$ calculates the current $I_{ij}$.


## Current Source

A current source $I_{ij}$ between nodes $i$ and $j$ with current flowing from $i$ to $j$ stamps the RHS vector $\vec{z}$ as

$$
\left[
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

## VCVS

## CCCS

## VCCS

A Voltage Controlled Current Source (VCCS) between nodes $i$ and $j$, producing a current flowing from $i$ to $j$ with magnitude $I_{ij}=G_m(V_p-V_q)$ where $V_p$ and $V_q$ are the controlling voltages, produces current

$G_m(V_p-V_q)$

out of node $i$ (negative) into node $j$ (positive). This causes the following additions to the matrix $\mathbf{Y}$:

$$
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


