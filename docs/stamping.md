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
\right]$$

$\mathbf{Y}$ is called the admittance matrix. $\vec{I}$ is the stimulus vector. This matrix equation can be solved for $\vec{v}$, which is a vector representing the node voltages. $\vec{v}$ is called the solution vector.

The matrix equation $\mathbf{Y} \cdot \vec{v}=\vec{I}$ can be solved using linear algebra methods. For this standard software packages are readily available.

Values in $\mathbf{Y}$ can have (frequency dependent) complex values for reactive components such as capacitors and inductors. Also values in $\vec{v}$ and $\vec{I}$ can have complex values. This way AC analysis is done.



# Modified Nodal Analysis

In MNA auxiliary equations (for voltage sources, inductors) diagonal entries are **not admittances**. They are whatever coefficient arises from the constitutive equation.


# Linear Components

## Resistor


## Capacitor

## Inductor


# Non-linear Components

## Diode


# Independent Sources

## Voltage Source


## Current Source


# Dependent Sources

## CCVS

## VCVS

## CCCS

## VCCS

# Compound Components


