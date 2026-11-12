# Probing Three-Body Neutrino Correlations Beyond the Phase-Space Approximation with Quantum Hardware

_Investigando correlações de três corpos entre neutrinos além da aproximação de espaço de fase com hardware quântico_

**Giovanna Fátima de Britto Vieira¹, Marco Ruas Sales Peixoto¹, Leonardo Villas Boas Fischel¹**

¹Instituto de Tecnologia e Liderança – Inteli, São Paulo – SP – Brazil

Advisors: Jose Erinaldo da Fonseca and Bryan Kano Ferreira

## Resumo

O sabor dos neutrinos em supernovas pode influenciar a explosão e a produção de elementos pesados. Este trabalho comparou a aproximação de espaço de fase (PSA) com a evolução exata em um modelo de dois sabores, com 4 a 16 neutrinos. O erro normalizado dos trios superou o dos pares nas 15 configurações com enumeração completa da PSA; sua tendência com a interação dependeu da janela temporal. No caso principal, a PSA recuperou 48% do cumulante exato. A mitigação ampliou a tolerância ao erro de leitura nas simulações. Circuitos IBM recuperaram 61%, 44% e 21% dos cumulantes em três pontos com 4, 6 e 8 qubits, superando a PSA, mas fora da margem de 0,01.

**Palavras-chave:** Neutrinos. Oscilações coletivas. Correlações de três corpos. Computação quântica. Aproximação de espaço de fase.

## Abstract

Neutrino flavor in supernovae can influence the explosion and heavy-element production. This work compared the phase-space approximation (PSA) with exact evolution in a two-flavor model with 4 to 16 neutrinos. Normalized triple errors exceeded pair errors in all 15 configurations with complete PSA enumeration; their interaction trend depended on the time window. In the primary case, PSA recovered 48% of the exact cumulant. Mitigation increased readout-error tolerance in simulations. IBM circuits recovered 61%, 44%, and 21% of the cumulants at three points with 4, 6, and 8 qubits, outperforming PSA but remaining outside the 0.01 margin.

**Keywords:** Neutrinos. Collective oscillations. Three-body correlations. Quantum computing. Phase-space approximation.

## Introduction

### Astrophysical context and motivation

Stars with an initial mass above about eight solar masses can undergo gravitational core collapse, whose bounce launches a shock that tends to stall and that neutrino absorption and matter motions can revive [Janka 2012, Abi et al. 2020]. A typical supernova emits about $10^{58}$ neutrinos, electrically neutral particles that interact weakly with matter, with characteristic energies of $10\,\mathrm{MeV}$, which carry more than 99% of the gravitational energy released [Abi et al. 2020]. The flavor evolution of these neutrinos changes the heating behind the shock and the neutron-to-proton ratio, which is relevant to nucleosynthesis, with effects that depend on the stellar configuration [Nagakura 2023, Akaho et al. 2026, Cowan et al. 2021]. The detection of SN 1987A and the prospects of DUNE, Hyper-Kamiokande, and JUNO reinforce the importance of predicting the emitted flavors [Vissani et al. 2010, Baum et al. 2022, Sarmah et al. 2026]. Near the core, the coherent interaction among neutrinos couples their evolutions and produces collective flavor oscillations, a quantum many-body problem [Duan et al. 2010].

### Problem, gap, and objective

The cost of exact evolution grows exponentially with the number of neutrinos. The mean-field approximation reduces this cost by neglecting connected correlations between particles [Cervia et al. 2019]. The phase-space approximation (PSA) incorporates effects beyond mean field through an ensemble of trajectories with random initial conditions [Lacroix et al. 2022] and has been validated for neutrinos through flavor averages, collective pair correlations, and reduced entropies [Lacroix et al. 2024, Mangin-Brinet et al. 2026]. Three-body neutrino cumulants have already been measured on hardware, without comparison with the PSA [Illa and Savage 2023]. In the literature examined, no pair-by-pair and triple-by-triple comparison of the connected three-body cumulants of the PSA with exact evolution was found.

Third-order cumulants matter because, in a Hamiltonian with pairwise interactions, the evolution of one-particle observables depends on two-body correlations, and the evolution of these depends on third-order moments, so that deviations in the triples can affect lower-order observables [Lacroix et al. 2024, Riccio and Balantekin 2026]. With up to sixteen neutrinos, the exact calculation is accessible on classical computers. The quantum stage assesses whether circuits distinguish the deviations of the PSA, which would be useful for validating approximations in systems without an exact solution, without assuming a computational advantage or extrapolating the results to larger systems.

This work seeks to determine in which regimes of interaction strength, system size, and evolution time the PSA reproduces the connected two- and three-body correlations and, when deviations exist, under which conditions of noise and number of measurements quantum circuits can distinguish them from the exact results. The model has two flavors and factorized pure-flavor initial states, and the mean field serves as an additional reference. The classical simulations cover four to sixteen neutrinos, and the circuits, four to eight. The ratio $\lambda=\mu/\bar{\omega}$ ranged from 0.1 to 10, where $\mu$ is the effective scale of the neutrino-neutrino interaction and $\bar{\omega}$ is the mean vacuum oscillation frequency. The supernova context motivates the model, and the conclusions are restricted to the simplified configurations examined.

Hypothesis **H1** is that the PSA reproduces the individual flavor probabilities and the two-body cumulants more accurately than the three-body cumulants. In the cases where the reference allows normalization, the normalized error in the triples tends to grow with the interaction strength. Hypothesis **H2** is that readout mitigation raises the noise level under which a circuit still distinguishes the PSA from the exact solution, with the same total measurement budget. Section 6 defines the metrics used to assess them.

## Theoretical background

### Flavor oscillations and the collective Hamiltonian

With two flavors, the states $|\nu_e\rangle$ and $|\nu_x\rangle$, where $\nu_x$ represents an effective combination of $\nu_\mu$ and $\nu_\tau$, are related to the mass states by a mixing angle $\theta$, and each neutrino can be described as a spin-1/2 in an effective field [Duan et al. 2010]. In dense environments, coherent forward scattering among neutrinos adds a flavor exchange between pairs, in the form of a scalar product between the flavor spins [Duan et al. 2010, Balantekin and Pehlivan 2007]. For $N$ neutrinos with discretized momenta, with $\hbar=c=1$ and in the flavor basis,

$$
H=\frac{1}{2}\sum_{i=0}^{N-1}\omega_i\,\mathbf{B}\cdot\boldsymbol{\sigma}_i
+\frac{\mu}{4N}\sum_{i<j}g_{ij}\,\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j,
\qquad
\omega_i=\frac{\Delta m^2}{2E_i},\qquad
\mathbf{B}=(\sin2\theta,0,-\cos2\theta),
\tag{1}
$$

where $\boldsymbol{\sigma}_i=(X_i,Y_i,Z_i)$ collects the Pauli matrices of neutrino $i$, $\Delta m^2$ is the difference between the squared masses, $E_i$ is the energy, $\mu$ is an effective interaction scale, proportional to $\sqrt{2}G_Fn_\nu$, with $G_F$ the Fermi constant and $n_\nu$ the neutrino density, and $g_{ij}$ incorporates the angular dependence $1-\cos\vartheta_{ij}$ between the propagation directions. The factor $1/N$ keeps the interaction energy per neutrino finite. With uniform $g_{ij}$, Equation (1) corresponds to the single-angle approximation [Pehlivan et al. 2011, Cervia et al. 2019], and the classical grid of this work uses $g_{ij}=1$.

The state of each neutrino is summarized by the polarization vector $\mathbf{P}_i=\langle\boldsymbol{\sigma}_i\rangle$, which in vacuum precesses around $\mathbf{B}$ with frequency $\omega_i$. The electron-flavor probability is $P_{e,i}=(1+m_i)/2$, with $m_i=\langle Z_i\rangle$ [Duan et al. 2010, Cervia et al. 2019]. With $|\nu_e\rangle=|0\rangle$ and $|\nu_x\rangle=|1\rangle$, each neutrino corresponds to a qubit, and the measurement of $Z_i$ distinguishes the two flavors. The state space has dimension $2^N$, which limits the exact evolution of large systems when symmetries are not exploited [Cervia et al. 2019], and Equation (1) describes a simplified closed system, without matter, antineutrinos, or collisions.

### Connected correlations and entanglement

A pure state of $N$ neutrinos is separable when it can be written as a product of individual states, and entangled otherwise. Starting from a product state, the interaction term of Equation (1) generates entanglement, whereas the vacuum term alone preserves the factorization. The correlations between measurement outcomes in the flavor basis are described by connected cumulants, which isolate the part of a joint moment that is not explained by lower-order moments [Riccio and Balantekin 2026]. For distinct particles,

$$
\begin{aligned}
C^{(2)}_{ij}(t)&=\langle Z_i Z_j\rangle_t-m_i(t)m_j(t),\\
C^{(3)}_{ijk}(t)&=\langle Z_i Z_j Z_k\rangle_t-m_i(t)m_j(t)m_k(t)\\
&\quad-C^{(2)}_{ij}(t)m_k(t)-C^{(2)}_{ik}(t)m_j(t)-C^{(2)}_{jk}(t)m_i(t).
\end{aligned}
\tag{2}
$$

Setting $C^{(3)}_{ijk}$ to zero is therefore not equivalent to setting $\langle Z_iZ_jZ_k\rangle$ to zero, and for a product state all cumulants of distinct particles vanish. Because they depend only on the distribution of measurement outcomes in the flavor basis, these cumulants do not, by themselves, certify entanglement, and the interest in the third-order ones lies mainly in their role in the dynamics.

### Mean field and the BBGKY hierarchy

The mean-field approximation replaces, in the interaction term, the operator of each partner by its average, $\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j\approx\boldsymbol{\sigma}_i\cdot\mathbf{P}_j+\mathbf{P}_i\cdot\boldsymbol{\sigma}_j-\mathbf{P}_i\cdot\mathbf{P}_j$ [Balantekin and Pehlivan 2007, Cervia et al. 2019]. Each polarization vector then precesses in a field that combines the vacuum term and the average of the others,

$$
\frac{d\mathbf{P}_i}{dt}=\Big[\omega_i\,\mathbf{B}+\frac{\mu}{2N}\sum_{j\neq i}g_{ij}\,\mathbf{P}_j\Big]\times\mathbf{P}_i .
\tag{3}
$$

The problem reduces to $3N$ coupled equations, and a product state remains a product, without entanglement or connected correlations. The deviations from exact evolution arise as the correlations grow [Lacroix et al. 2022].

In exact evolution, the Ehrenfest equations do not close. For component $b$ of the polarization vector,

$$
\frac{dP_i^{b}}{dt}=\Big(\Big[\omega_i\mathbf{B}+\frac{\mu}{2N}\sum_{j\neq i}g_{ij}\mathbf{P}_j\Big]\times\mathbf{P}_i\Big)^{b}
+\frac{\mu}{2N}\sum_{j\neq i}g_{ij}\,\epsilon_{bac}\,C^{ac}_{ji},
\qquad C^{ac}_{ji}=\langle\sigma_j^a\sigma_i^c\rangle-P_j^aP_i^c,
\tag{4}
$$

where $\epsilon_{bac}$ is the Levi-Civita symbol and the repeated indices $a$ and $c$ are summed over. The mean field corresponds to setting the two-body cumulants $C^{ac}_{ji}$ to zero, whose equations depend, in turn, on three-body cumulants, and so on, in a hierarchy of the Bogoliubov–Born–Green–Kirkwood–Yvon (BBGKY) type [Volpe et al. 2013, Lacroix and Ayik 2014]. A closure of order $m$ sets the cumulants of order $m+1$ to zero. The mean field corresponds to $m=1$, and the second-order closure of Riccio and Balantekin (2026) sets all components of the three-body cumulants to zero. In Equation (4), each pair contributes with coefficient $\mu/(2N)$, summed over the $N-1$ partners, so that the weight of the correlation terms grows with the interaction. This structure motivates hypothesis H1 without proving it, because the expectation depends on the initial state and on the time window and does not follow from the PSA setting higher cumulants to zero.

### Phase-space approximation

The PSA turns the quantum evolution into a statistical problem [Lacroix et al. 2022, Lacroix et al. 2024]. Classical initial conditions $\mathbf{s}_i^{(\ell)}(0)$ are sampled so that their means and fluctuations reproduce those of the initial quantum state. Each trajectory $\ell$ evolves independently according to Equation (3), with $\mathbf{P}_i$ replaced by $\mathbf{s}_i^{(\ell)}$, and the observables are estimated by averages of products of the components $s^{z,(\ell)}_i(t)$ over the $N_{\mathrm{traj}}$ trajectories. The idea comes from the stochastic mean field of nuclear physics [Lacroix and Ayik 2014]. The cost per trajectory is polynomial in $N$, and the statistical error of the averages decreases as $1/\sqrt{N_{\mathrm{traj}}}$.

For product states with one neutrino per beam, Lacroix et al. (2024) proposed a bivalued sampling, in which the component of $\mathbf{s}_i$ along the initial flavor is fixed and the two transverse components independently take the values $\pm1$ with equal probability,

$$
\mathbf{s}_i^{(\ell)}(0)=\mathbf{n}_i+x_i^{(\ell)}\mathbf{u}_i+y_i^{(\ell)}\mathbf{v}_i,\qquad x_i^{(\ell)},\,y_i^{(\ell)}\in\{-1,+1\},
\tag{5}
$$

where $\mathbf{n}_i=\pm\hat{z}$ indicates the initial flavor and $\mathbf{u}_i$, $\mathbf{v}_i$ complete an orthonormal basis. This choice reproduces $\overline{\mathbf{s}_i}=\mathbf{n}_i$ and $\overline{s_i^a s_i^b}=\delta_{ab}$, like the symmetrized quantum second moments of $\boldsymbol{\sigma}_i$, and starts the full distribution without cumulants between distinct particles.

Although each trajectory is represented by classical vectors, the ensemble develops correlations between particles, because trajectories with distinct initial conditions separate along the evolution. According to Lacroix et al. (2024), the PSA is equivalent to a non-truncated BBGKY hierarchy that differs from the exact one only at the two-body level. Unlike the second-order closure, which sets the three-body cumulants to zero, the PSA does not impose $C^{(3)}=0$. The agreement of the PSA cumulants with the exact ones is what this work examines.

### Digital quantum simulation and Trotterization

In digital quantum simulation, the evolution operator $U(t)=e^{-iHt}$ is approximated by a sequence of one- and two-qubit gates [Lloyd 1996, Nielsen and Chuang 2010]. Equation (1) separates into one-body terms, which generate single-qubit rotations around $\mathbf{B}$, and pair terms, $H_{ij}=\tfrac{\mu g_{ij}}{4N}\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j$. Since $\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j=2\,\mathrm{SWAP}_{ij}-\mathbb{1}$, $e^{-iH_{ij}\delta}$ is a single two-qubit gate, equivalent to a partial flavor swap, and requires at most three CNOTs [Vatan and Williams 2004]. Because all pairs interact, the number of two-qubit gates per step grows with $N^2$, and processors with limited connectivity additionally require routing SWAP gates [Hall et al. 2021, Amitrano et al. 2023].

Because the terms do not commute with one another, the evolution is divided into $r$ steps of duration $\delta=t/r$. For $H=\sum_{\gamma=1}^{\Gamma}H_\gamma$, the symmetric second-order Suzuki formula is

$$
S_2(\delta)=e^{-iH_1\delta/2}\cdots e^{-iH_\Gamma\delta/2}\,e^{-iH_\Gamma\delta/2}\cdots e^{-iH_1\delta/2},
\qquad U(t)\approx S_2(t/r)^r,
\tag{6}
$$

with error $O(t^3/r^2)$ over the total interval [Childs et al. 2021]. Pair terms that share a particle have commutators involving three-body operators, which makes the discretization error relevant for the triples. Increasing $r$ reduces this error but deepens the circuit and increases its exposure to noise.

### Measurement, noise, and readout mitigation

Measurement in the computational basis produces bit strings, and the expectation value of $Z_S=\prod_{i\in S}Z_i$, for a set of qubits $S$, is estimated by the average parity of the bits of $S$ over $m$ repetitions [Nielsen and Chuang 2010]. The same counts provide $m_i$, $\langle Z_iZ_j\rangle$, and $\langle Z_iZ_jZ_k\rangle$, with statistical error proportional to $1/\sqrt{m}$, and the uncertainties of the cumulants depend on the covariances between these moments [Hall et al. 2021, Cai et al. 2023].

On current processors, without error correction, noise limits the useful depth of the circuits [Preskill 2018]. A usual model of gate error is the depolarizing channel of probability $p$, which multiplies the expectation value of any nontrivial Pauli operator by $1-p$ [Nielsen and Chuang 2010]. At readout, each bit can be flipped with probability $\varepsilon$, independently across qubits, which results in $\langle Z_S\rangle_{\mathrm{meas}}=(1-2\varepsilon)^{|S|}\langle Z_S\rangle$, and the same factor $(1-2\varepsilon)^3$ attenuates $C^{(3)}$. Higher-order correlations therefore suffer stronger attenuation.

In readout mitigation, the relation between the ideal and measured distributions is described by a response matrix that, assuming independent errors across qubits, factorizes into single-qubit matrices, which are estimated by calibration circuits and inverted on the measured frequencies [Bravyi et al. 2021]. The result may contain negative quasiprobabilities, which provide unbiased estimates of linear moments when the response matrix is known exactly. The estimation of this matrix and the calculation of the cumulants can introduce finite bias. The inversion increases the variance, and the calibration consumes part of the measurement budget [Bravyi et al. 2021, Cai et al. 2023]. Readout mitigation does not correct gate errors, which require techniques such as zero-noise extrapolation [Cai et al. 2023].

## Literature review

### The many-body problem and the limits of mean field

With exact solutions for up to nine neutrinos, Cervia et al. (2019) related the differences between mean field and exact evolution to the development of entanglement, with a strong dependence on the initial conditions. Rrapaj (2020) compared multiangle exact solutions with the mean field, including connected pair correlations, and indicated that the expected disagreement is largest when the net flavor polarization is zero, as in the state with half of the neutrinos in each flavor adopted in this research. There are, however, limits to extrapolating these results. In a two-beam model, the mean field recovers one-body observables in the limit of many neutrinos [Martin et al. 2022], and closed systems with few neutrinos are not sufficient to validate or invalidate it in open astrophysical sources [Shalgar and Tamborra 2023]. These works justify the focus on correlations, which the mean field neglects by construction, and the restriction of the conclusions to small closed systems.

### Methods beyond mean field

The PSA offers a polynomial-cost alternative to exact evolution. Lacroix et al. (2022) applied it to a two-beam model, in which the method reproduced averages, fluctuations, and one- and two-neutrino entropies, but not the long-time oscillations of the fluctuations. The extension to multiple beams used an arrangement similar to that of this work, with four, eight, and twelve neutrinos, half in each flavor, and interaction between all pairs. In it, the individual flavor averages were overdamped at long times, whereas the collective correlation $C_{ZZ}$, which sums the covariances of all pairs, and the average one-neutrino entropy were well reproduced [Lacroix et al. 2024]. Pair-by-pair covariances, three-body cumulants, and the dependence on the interaction strength were not assessed. The three-flavor version reproduced flavor populations and entropies of exact solutions for up to eight neutrinos [Mangin-Brinet et al. 2026].

Outside neutrinos, de Correc et al. (2026) applied the PSA to qubit registers in Ising models and observed a loss of accuracy in two-qubit correlations and in entropies of larger subsystems, especially at strong coupling, which qualitatively anticipates hypothesis H1, without involving connected three-body cumulants or the neutrino Hamiltonian. Along the line of the BBGKY hierarchy, the second-order closure of Riccio and Balantekin (2026) treats about one hundred neutrinos at polynomial cost, but its comparison with exact evolution was restricted to four neutrinos in three flavors.

### Quantum simulation of collective oscillations

Hall et al. (2021) simulated four neutrinos on an IBM processor, with readout mitigation and zero-noise extrapolation, and Amitrano et al. (2023) showed that the all-to-all connectivity of trapped ions reduces the depth of second-order Trotter circuits, with executions of up to eight neutrinos. Illa and Savage (2023) measured connected two- and three-body correlations in systems of up to twelve neutrinos, with the same definition of cumulants as Equation (2) and the same initial state with half in each flavor. With 240 measurements on the trapped-ion processor and 1,200 on the emulator, most three-body cumulants were compatible with zero, which indicates that the measurement budget limits the resolution of these observables. Kiss et al. (2026) used IBM processors with up to 112 qubits to study thermalization and compared the results with the PSA, but only for single-qubit observables.

### Synthesis and positioning

_Table 1 - Related works and observables compared. MF: mean field; "collective": aggregate quantity, with its own definition in each study; "set to zero": cumulant made equal to zero by the closure. All treat two flavors, except Mangin-Brinet et al. (three), Riccio and Balantekin (two and three), and de Correc et al. (qubits in Ising models). Source: prepared by the authors._

| Work                        | Methods                  |   Max. $N$ |    $P_e$     | $C^{(2)}$  |  $C^{(3)}$  | Platform      |
| --------------------------- | ------------------------ | ---------: | :----------: | :--------: | :---------: | ------------- |
| Rrapaj (2020)               | Exact, MF                |         20 |     Yes      |   Pairs    |      —      | Classical     |
| Lacroix et al. (2022)       | Exact, MF, PSA           |        100 |     Yes      | Collective |      —      | Classical     |
| Lacroix et al. (2024)       | Exact, PSA               |         12 |     Yes      | Collective |      —      | Classical     |
| Mangin-Brinet et al. (2026) | Exact, MF, PSA           |          8 |     Yes      |     —      |      —      | Classical     |
| de Correc et al. (2026)     | Exact, MF, PSA           |         10 |     Yes      |  Average   |      —      | Classical     |
| Riccio and Balantekin (2026) | BBGKY, MF, exact        |  4 (exact) |     Yes      |    Yes     | Set to zero | Classical     |
| Illa and Savage (2023)      | Exact, circuit           |         12 |     Yes      |    Yes     |     Yes     | Trapped ions  |
| Kiss et al. (2026)          | Circuit, PSA             |        112 | Single qubit |     —      |      —      | IBM           |
| This work                   | Exact, MF, PSA, circuit  |         16 |     Yes      |   Pairs    |   Triples   | Aer, IBM      |

Table 1 shows that three-body cumulants appear only in hardware measurements without comparison with approximations [Illa and Savage 2023] or set to zero by construction in a closure of the hierarchy [Riccio and Balantekin 2026], and in the literature located no work was identified that compares the connected three-body cumulants of the PSA with exact evolution. This work makes this comparison pair by pair and triple by triple, controlling the system size, the ratio $\lambda$, and the sampling, discretization, and measurement uncertainties, and assesses whether quantum circuits with noise and readout mitigation distinguish the deviations of the PSA.

## Methodology

The study compares four descriptions of the same dynamics. Exact evolution serves as the reference. The mean field and the PSA are the approximations assessed, and the Trotterized circuits represent the quantum alternative. All use the dimensionless form of Equation (1), with $\tau=\bar{\omega}t$, $\lambda=\mu/\bar{\omega}$, and $\widetilde{\omega}_i=\omega_i/\bar{\omega}$,

$$
\frac{H}{\bar{\omega}}=\frac{1}{2}\sum_{i=0}^{N-1}\widetilde{\omega}_i\,\mathbf{B}\cdot\boldsymbol{\sigma}_i
+\frac{\lambda}{4N}\sum_{i<j}g_{ij}\,\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j .
\tag{7}
$$

**Exact evolution.** The state of $2^N$ amplitudes is propagated by the action of the exponential of the sparse Hamiltonian matrix on the state vector (`expm_multiply`, SciPy). To verify the construction of this matrix, a dense Hamiltonian assembled independently, by Kronecker products, was compared with it in a system of four neutrinos with generic couplings and states.

**Mean field and PSA.** Equations (3) and (5) are integrated by fourth-order Runge–Kutta (RK4) with fixed substeps between consecutive instants. The PSA is organized in blocks of 4,096 trajectories, each with its own seed. The moments $m_i$, $\langle Z_iZ_j\rangle$, and $\langle Z_iZ_jZ_k\rangle$ are summed across the blocks before the cumulants are calculated, because cumulants calculated in each block and then averaged would have a bias of order $1/N_{\mathrm{traj}}$.

**Circuits.** The circuits apply the second-order Suzuki formula of Equation (6), with one two-qubit gate per pair and per half step. The Qiskit implementation was compared with an independent state-vector emulator. The ideal measurements are sampled from the exact distribution of the circuit. The noisy executions use the Qiskit Aer simulator with a density matrix and the `ibm_kingston` processor. Readout mitigation follows Bravyi et al. (2021), with matrices calibrated by the states $|0000\rangle$ and $|1111\rangle$, and preserves negative quasiprobabilities.

**Observables.** The probabilities $P_{e,i}$ and the cumulants $C^{(2)}_{ij}$ and $C^{(3)}_{ijk}$ of Equation (2) are assessed for all distinct individuals, pairs, and triples. Times and sets of particles from the same evolution are not independent replicates. The resampling units are the PSA blocks or the hardware jobs, depending on the analysis.

**Controls.** Before the comparison, each stage went through checks with limits fixed in advance (Table 5). The controls include the reproduction of a published PSA result, the absence of cumulants without interaction, the coincidence between exact and mean field without interaction, the convergence of RK4, the standard error of the PSA across seeds, and the Trotter error of the ideal circuits. Two controls failed in the first execution. In the first, the standard error of $C^{(3)}$ across five PSA blocks exceeded $10^{-2}$ in three of the six configurations tested, and the number of blocks was raised to twenty in all configurations, which reduced the largest standard error to $5.11\times10^{-3}$. In the second, the ideal circuit with 112 steps missed $C^{(3)}$ by $4.0\times10^{-3}$ at $\lambda=10$, $\tau=4$, above the limit of $10^{-3}$, and this configuration came to use 448 steps. At the same interaction, the PSA reference at $\tau=2$ went from 12 to 24 RK4 substeps. No result was discarded, and the repeated controls passed after these changes. These limits refer to the configurations checked; the residuals of the additional hardware points are reported separately.

## Experiments and parameters

### Classical grid

Table 2 summarizes the grid used for H1. The association between frequency and initial flavor is fixed, with the lowest frequencies in the electron flavor.

_Table 2 - Parameters of the classical grid._

| Parameter              | Values                                                                        |
| ---------------------- | ----------------------------------------------------------------------------- |
| Size                   | $N=4,6,8$ (main) and $N=12,16$ (extension)                                    |
| Interaction            | $\lambda=0.1;\ 0.3;\ 1;\ 3;\ 10$                                              |
| Frequencies and mixing | $\widetilde{\omega}_i=0.7+0.6\,i/(N-1)$; $\theta=0.2$ rad                     |
| Couplings              | $g_{ij}=1$ for $i\neq j$                                                      |
| Initial state          | First half of the neutrinos in $\nu_e$ and the second half in $\nu_x$         |
| Time                   | $0\leq\tau\leq10$, 201 instants, 12 RK4 substeps per interval                 |
| PSA                    | 20 blocks of 4,096 trajectories (81,920 in total), seeds 10,001 to 10,020     |

The reproduction of Lacroix et al. (2024) uses Figure 2(c) of that study, with eight neutrinos and 10,000 trajectories, in a configuration distinct from Table 2. The coordinates were extracted from the published figure, which adds a reading uncertainty to the deviations.

### Circuits and noise

The ideal circuits use $N=4,6,8$, the five interactions, and twenty blocks of $m=1{,}024$, $4{,}096$, or $16{,}384$ measurements per instant. The noisy executions in Aer are restricted to $N=4$, to the triple $(0,1,2)$, and to $\tau=1,2,4$, with seven time intervals and 16 Trotter steps per interval. The primary case is $N=4$, $\lambda=3$, $\tau=2$, in which the exact cumulant is large and the PSA departs from it.

Table 3 presents the depth of the circuits used in the simulator and the smallest number of steps that keeps the Trotter error of $C^{(3)}$ below $10^{-3}$. The 112 steps of the Aer executions result in 4,032 CNOTs in the simulator, without connectivity restrictions, and in 6,048 after compilation to a linear chain of qubits, close to the connectivity of the hardware. In the primary case, 12 steps are enough and reduce the circuit to 648 CNOTs. The first hardware execution already used a shorter discretization, with 2 steps per interval, 14 in total, and a Trotter error of $7.2\times10^{-4}$. Compiled on the processor, this circuit has 672 CZ gates and depth 2,918, with a logical mapping to the physical qubits $(109,110,118,108)$.

_Table 3 - Circuits of the triple $(0,1,2)$ with $N=4$, compiled to `rz`, `sx`, `x`, and `cx` gates on a linear chain (Qiskit, optimization level 1). The first three numerical columns refer to the discretization used in Aer and the last two, to the smallest number of steps with a Trotter error in $C^{(3)}$ below $10^{-3}$._

| $\lambda$ | $\tau$ |  Steps |         Depth |     CNOTs | Min. steps | CNOTs (min.) |
| --------: | -----: | -----: | ------------: | --------: | ---------: | -----------: |
|   0.1–0.3 |    1–4 |    112 | 11,989–15,909 |     6,048 |        1–2 |       54–108 |
|         1 |      1 |    112 |        11,989 |     6,048 |          1 |           54 |
|         1 |      2 |    112 |        11,989 |     6,048 |          3 |          162 |
|         1 |      4 |    112 |        11,989 |     6,048 |          6 |          324 |
|         3 |      1 |    112 |        11,989 |     6,048 |          5 |          270 |
|     **3** |  **2** |**112** |    **11,989** | **6,048** |     **12** |      **648** |
|         3 |      4 |    112 |        11,989 |     6,048 |         22 |        1,188 |
|        10 |      1 |    112 |        11,989 |     6,048 |         20 |        1,080 |
|        10 |      2 |    112 |        11,989 |     6,048 |         37 |        1,998 |
|        10 |      4 |    448 |        47,941 |    24,192 |        224 |       12,096 |

Table 4 lists the noise models. The light and moderate profiles reproduce the original executions with 112 steps. The sweep uses the 12-step circuit of the primary case and varies separately the depolarization of the two-qubit gates, $p$, and the readout error, $\varepsilon$, to test H2.

_Table 4 - Noise models in Qiskit Aer. The single-qubit depolarization is $p/10$ and acts on `sx` and `x`; the two-qubit depolarization acts on `cx`._

| Model    | Steps | Depolarization $p$                                                  | Readout error $\varepsilon$             |
| -------- | ----: | ------------------------------------------------------------------- | --------------------------------------- |
| Light    |   112 | $10^{-3}$                                                           | 0.01                                    |
| Moderate |   112 | $10^{-2}$                                                           | 0.03                                    |
| Sweep    |    12 | $0;\ 10^{-5};\ 3\times10^{-5};\ 10^{-4};\ 3\times10^{-4};\ 10^{-3}$ | $0;\ 0.005;\ 0.01;\ 0.02;\ 0.03;\ 0.05$ |

The budget per method is $M=20m$, with $m=16{,}384$. The raw method uses all measurements on the signal circuit. The mitigated method uses $3m/4$ measurements on the signal and $m/8$ on each calibration, so that the calibration consumes part of the same budget. In the sweep, Aer calculates the probability distribution with gate noise, the readout error is applied as a tensor product of bit-flip matrices, and the counts are drawn from this distribution. The first execution on `ibm_kingston` used the primary case with 14 steps, twenty blocks, and the same budget. The hardware experiment was then redone with a shorter circuit. The instant $\tau=1.5$ was chosen after the first execution, because at it the exact cumulant of the triple $(0,1,2)$ is still $-0.159$, the PSA recovers only 34% of it, and the smallest number of steps with a Trotter error below $10^{-3}$ is 2, with an error of $8.2\times10^{-4}$. Compiled on the processor, this circuit has 78 CZ gates and depth 294, with mapping $(142,143,144,136)$, about nine times fewer two-qubit gates than that of the first execution. Because the choice of the instant came after the first results, an exploratory screening on the processor preceded the confirmation, which was made with twenty jobs of 16,384 measurements and new seeds, with gate twirling and without readout mitigation. In this case, the reference PSA is calculated with the 256 initial conditions of the bivalued sampling, which eliminates its Monte Carlo error.

Two points with six and eight qubits were executed on the same processor, in a configuration different from the grid. In them, the neutrinos form two beams, with coupling only between beams, of $g_{ij}=5/3$ for $N=6$ and $7/4$ for $N=8$, so that the average over all pairs is 1. The initial flavors alternate, $\lambda=10$, and the circuits have two Trotter steps, with $\tau=0.55$ and the triple $(0,1,2)$ for $N=6$ and $\tau=0.65$ and the triple $(1,3,5)$ for $N=8$. Compiled, they total 204 and 429 CZ gates, with depths 540 and 927 and mappings $(136,123,122,124,143,144)$ and $(123,136,124,122,143,142,144,141)$, respectively. The Trotter error of $C^{(3)}$ is $1.3\times10^{-3}$ and $1.3\times10^{-2}$. The points were chosen by classical calculations, before any execution at these sizes, in a search over 36 combinations of size, interaction, initial state, and geometry that favored large exact signals and large PSA deviations in short circuits. Five pilot jobs of 4,096 measurements per size preceded a confirmation with the same circuits, made in twenty jobs with both circuits, 4,096 measurements per circuit, alternating order, and five calibration windows. The confirmation compares the absolute error of the hardware with that of the PSA, calculated with all $4^N$ initial conditions, and with that of the prediction $C^{(3)}=0$, with four simultaneous 98.75% intervals, by the Bonferroni correction.

_Table 5 - Numerical controls. Maximum values observed over all configurations of each control._

| Control                                   |              Limit |     Maximum observed |
| :---------------------------------------- | -----------------: | -------------------: |
| Published reproduction: exact             |   $2\times10^{-2}$ | $1.41\times10^{-3}$  |
| Published reproduction: PSA               |   $6\times10^{-2}$ | $2.99\times10^{-2}$  |
| Exact: independent dense Hamiltonian      |         $10^{-10}$ | $2.26\times10^{-16}$ |
| No interaction: exact $C^{(3)}$           |         $10^{-10}$ | $1.33\times10^{-15}$ |
| Qiskit versus emulator                    |         $10^{-10}$ | $2.80\times10^{-12}$ |
| RK4 refinement: $P_e$                     |          $10^{-6}$ | $5.16\times10^{-8}$  |
| RK4 refinement: cumulants                 |          $10^{-5}$ | $1.26\times10^{-7}$  |
| PSA standard error: $C^{(3)}$             |          $10^{-2}$ | $5.11\times10^{-3}$  |
| Ideal Trotter: $C^{(3)}$                  |          $10^{-3}$ | $8.91\times10^{-5}$  |

## Evaluation metrics

### Normalized error and hypothesis H1

For $T$ instants and $n_q$ sets of particles of order $q$, let $O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)$ be the exact reference and $\widehat O_{q,\alpha}(\tau_\ell)$ the PSA estimate. The error and the signal scale are

$$
E_q^2=\max\!\left\{0,\ \frac{1}{Tn_q}\sum_{\ell,\alpha}\left[\widehat{O}_{q,\alpha}(\tau_\ell)-O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)\right]^2-\overline{\sigma^2_q}\right\},\qquad
S_q^2=\frac{1}{Tn_q}\sum_{\ell,\alpha}\left[O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)\right]^2,
\tag{8}
$$

where $\overline{\sigma^2_q}$ is the average variance of the PSA estimator, estimated by the dispersion across the twenty blocks divided by twenty. Without this term, the squared error would include the Monte Carlo noise of the PSA itself, which is comparable to the signal when the interaction is weak and would inflate $E_q$ precisely where the cumulants are small. The normalized error is $R_q=E_q/S_q$, with $q=1,2,3$, for $S_q\geq10^{-4}$; below this floor, the absolute error is used. A larger normalized error does not necessarily imply a larger absolute error. For the flavor probabilities, $m_i=2P_{e,i}-1$ is used, so that $S_1$ measures the departure of $P_e$ from $1/2$. The first part of H1 is assessed by $D=R_3-R_2$ and by $D_1=R_3-R_1$, with positive values indicating that the PSA errs more in the triples.

The 95% intervals come from 2,000 bootstrap replicates of the twenty blocks. Because the corrected statistic estimates the systematic error of the PSA, and in the bootstrap world the mean of the blocks has no noise of its own, the basic interval $[\widehat D-q_{97.5},\ \widehat D-q_{2.5}]$ is used, where $q_{2.5}$ and $q_{97.5}$ are percentiles of the difference between each corrected replicate and the uncorrected value calculated at the mean of the blocks, which is the reference of the bootstrap world. The same procedure applies to $D_1$ and to the slopes. When the noise of the PSA exceeds 1.5 times the estimated systematic error, the configuration is flagged as noise-dominated.

The second part of H1, the growth of the triple error with the interaction, is measured by the slope $b_N$ of the linear regression of $R_3$ on $\log_{10}\lambda$, for each $N$. The interval of $b_N$ uses the same bootstrap replicates, with seeds paired across the interactions, and this part of H1 receives local support when the nominal 95% interval of $b_N$ lies above zero. A positive slope does not require monotonic growth. The intervals are pointwise, without simultaneous adjustment across configurations, and their count does not confirm H1 globally.

### Criterion for the circuits and hypothesis H2

For a noisy circuit, let $I_{\mathrm{PSA}}$ be the 95% interval of circuit minus PSA and $[L,U]$ that of circuit minus exact, both obtained from 2,000 multinomial replicates of the aggregated counts, with the calibration re-estimated in each replicate and the PSA blocks resampled. The circuit distinguishes the PSA from the exact result when

$$
0\notin I_{\mathrm{PSA}}
\quad\text{and}\quad
[L-r,U+r]\subseteq[-0.01,\ 0.01],
\tag{9}
$$

where $r$ adds the Trotter error of the ideal circuit to a numerical tolerance of $10^{-5}$. Calibrations with a condition number above 10 make the case unresolved. As a complementary criterion, which does not require recovering the exact value, the absolute error of the circuit is compared with that of the PSA by $\Delta=|\widehat C^{(3)}_{\mathrm{circ}}-C^{(3)}_{\mathrm{ex}}|-|C^{(3)}_{\mathrm{PSA}}-C^{(3)}_{\mathrm{ex}}|$, with an interval obtained by resampling the jobs. The value $\Delta<0$ indicates that the circuit was closer to the exact result than the approximation. In the initial sweep, the highest approved level describes the points assessed, without guaranteeing a monotonic threshold. In the additional analysis with 78 CZ, the threshold is delimited by the first failure, with any later successes kept as fluctuations. H2 receives support when the recovery region of the mitigated method exceeds that of the raw method.

The additional analysis with 78 CZ uses 32 twirling variants and 100 synthetic campaigns per condition. Its primary outcome is the circuit-minus-exact interval contained in $\pm0.01$, without the additional widening by $r$ of Equation (9), because the Trotter bias already remains in the error. In the confirmation with six and eight qubits, 10,000 replicates jointly resample the twenty jobs, preserving the two circuits of each job, without a new internal multinomial sampling.

## Experimental results

### The PSA recovers half of the triple cumulant in the primary case

In the primary case ($N=4$, $\lambda=3$, $\tau=2$), the exact cumulant of the triple $(0,1,2)$ is $C^{(3)}=-0.316$. The PSA, with three sets of 81,920 trajectories, gave $-0.156$, $-0.152$, and $-0.147$, and their mean is $-0.151\pm0.002$. The approximation therefore recovers 48% of the exact cumulant, a deviation of 0.165, more than eighty times the standard error. In the window $0\leq\tau\leq10$ of this configuration, the normalized error of the pairs is $R_2=0.419$, against $R_3=0.948$ for the triples. The deviation does not come from the sampling of the PSA or from the discretization, because the standard error is about eighty times smaller than the deviation and the integration controls also lie below it (Table 5).

### PSA accuracy in pairs and triples

Table 6 presents $D$ for the 25 configurations, with the sampling noise of the PSA subtracted.

_Table 6 - Difference $D=R_3-R_2$ between the normalized errors of triples and pairs of the PSA, with 95% interval. Positive values indicate a larger error in the triples. The asterisk marks the configurations in which the sampling noise of the PSA exceeds 1.5 times the estimated systematic error._

| $N$ | $\lambda=0.1$ | $\lambda=0.3$ | $\lambda=1$ | $\lambda=3$ | $\lambda=10$ |
| ---: | :---: | :---: | :---: | :---: | :---: |
| 4 | −0.180 [−0.326, −0.048] | 0.267 [0.237, 0.293] | 0.430 [0.417, 0.443] | 0.529 [0.524, 0.535] | 0.602 [0.599, 0.605] |
| 6 | 0.109 [−0.052, 0.257] | 0.306 [0.270, 0.346] | 0.359 [0.347, 0.370] | 0.625 [0.617, 0.632] | 0.752 [0.747, 0.756] |
| 8 | 0.264 [0.062, 0.430] | 0.358 [0.294, 0.405] | 0.362 [0.351, 0.373] | 0.505 [0.495, 0.513] | 0.936 [0.933, 0.939] |
| 12 | 0.347 [−0.007, 0.664]$^{*}$ | 0.445 [0.376, 0.501] | 0.311 [0.297, 0.323] | 0.371 [0.361, 0.379] | 0.720 [0.710, 0.729] |
| 16 | 0.695 [0.041, 1.282]$^{*}$ | 0.583 [0.476, 0.669] | 0.239 [0.228, 0.250] | 0.174 [0.163, 0.184] | 0.517 [0.508, 0.526] |

The nominal 95% interval of $D$ lay above zero in 22 of the 25 configurations. The exceptions all occurred with the weakest interaction, $\lambda=0.1$. For $N=4$, the interval lay below zero, with $D=-0.180$ $[-0.326,\ -0.048]$, so that in this configuration the PSA erred more in the pairs than in the triples. For $N=6$ and $N=12$, the sign was undetermined. At this interaction, the exact cumulants are small, with a scale of $10^{-3}$ in the triples, and for $N=12$ and $N=16$ the sampling noise of the PSA exceeded the systematic error, which makes these two values uninformative with 81,920 trajectories.

The correction for sampling noise changed in a relevant way only the configurations with $\lambda\leq0.3$. Without it, the squared error included the Monte Carlo variance of the PSA, and five estimates of $D$ lay outside their own bootstrap intervals, because each replicate, by repeating blocks, added noise and shifted the distribution upward. For $N=16$, $\lambda=0.1$, for example, the uncorrected value was $2.062$, outside the interval $[2.425,\ 3.280]$, and the corrected value is $0.695$. For $\lambda\geq1$, the sampling noise is small compared with the systematic error, and the corrected values differ from the original ones by at most 0.002.

The triples were also reproduced less accurately than the flavor probabilities. The interval of $D_1=R_3-R_1$ lay above zero in the 25 configurations. With $\lambda\leq0.3$, the normalized error of the probabilities did not exceed 0.011, whereas that of the triples lay between 0.50 and 1.15. With $\lambda=10$, however, $R_1$ reached values between 0.53 and 1.01, because the PSA damps the oscillations of the individual probabilities at strong coupling, as reported by Lacroix et al. (2024), and the advantage of the probabilities over the triples fell to between 0.09 and 0.24.

The normalized error of the triples grew with the interaction in the smaller systems. The slope of $R_3$ per decade of $\lambda$ was $b_{4}=0.264$ $[0.215,\ 0.319]$, $b_{6}=0.162$ $[0.101,\ 0.229]$, and $b_{8}=0.150$ $[0.061,\ 0.260]$. For $N=12$, the slope was $b_{12}=0.042$ $[-0.144,\ 0.264]$, and for $N=16$, $b_{16}=-0.260$ $[-0.587,\ 0.101]$, both without a definite trend. At these two sizes, $R_3$ fell from between 0.70 and 1.15 with $\lambda\leq0.3$ to between 0.24 and 0.44 with $\lambda$ between 1 and 3 and rose again at $\lambda=10$.

As a control, the grid with $N=4,6,8$ was recalculated with the PSA evaluated at all $4^N$ initial conditions, without Monte Carlo error, in a shorter window, $0\leq\tau\leq3$, with 61 instants. In this grid, $D$ was positive in the 15 configurations, which supports the comparison between triples and pairs in this window without depending on the correction for sampling noise. The slopes of $R_3$, however, were $b_4=0.091$, $b_6=0.006$, and $b_8=-0.115$, and at no size did $R_3$ grow monotonically with $\lambda$. For $N=4$, $\lambda=10$, the PSA erred more than the prediction $C^{(3)}=0$. The growth observed in the full window therefore depends on the inclusion of the long times. The first part of H1 receives local support in the comparisons described. The increasing trend of the second part appears for $N\leq8$ in the window $0\leq\tau\leq10$ but does not hold as a rule at the initial times.

### Measurement budget

In the ideal circuits, the RMSE of $C^{(3)}$ with respect to the exact result decreased with each increase in budget in the fifteen configurations (Figure 1). From 1,024 to 16,384 measurements per block, the reduction was by a factor of 3.75 to 4.19, close to the factor of four expected from the $m^{-1/2}$ dependence. The error of the ideal circuits is therefore dominated by the measurement statistics. With the largest budget, the RMSE lay between $3.4\times10^{-4}$ and $1.8\times10^{-3}$, well below the deviation of the PSA in the primary case.

![RMSE of C3 of the ideal circuits as a function of the measurements per block, for N = 4, 6, and 8 and five interaction strengths.](figuras/figura-orcamento-medicoes.svg)

_Figure 1 - RMSE of $C^{(3)}$ of the ideal circuits with respect to the exact result, over all instants and triples, with twenty blocks of $m$ measurements. The bars indicate the 95% range in 500 independent repetitions of the experiment._

### Noise, mitigation, and hardware

Figure 2 shows the estimate of $C^{(3)}$ in the primary case under the noise sweep. Without gate noise, the raw method distinguished the PSA from the exact result only with perfect readout, because the attenuation $(1-2\varepsilon)^3$ already shifts the estimate outside the 0.01 margin with $\varepsilon=0.005$. Readout mitigation kept the estimate within the margin up to $\varepsilon=0.03$, and at $\varepsilon=0.05$ the result oscillated between the gate-noise levels, a sign that the increased variance of the inversion brings the interval close to the edge of the margin. For readout noise, therefore, mitigation raised the threshold, as H2 predicts.

Gate noise produced a different picture. Without readout error, the highest depolarization level that satisfied the criterion was $p=10^{-5}$ for the raw method and $p=3\times10^{-5}$ for the mitigated method, and with $p=10^{-4}$ both methods were already outside the margin. The difference at $3\times10^{-5}$ is at the limit of the resolution of the sweep, because at this level the mitigated method passed in only three of the six readout errors. With $\varepsilon=0.03$, the raw method did not reach the margin at any level, and the mitigated method did so up to $p=10^{-5}$. Readout mitigation does not treat gate noise, and the support for H2 is restricted to readout error. With $p=10^{-3}$ in the depolarizing model adopted, and $\varepsilon=0.03$, the mitigated circuit estimated $C^{(3)}=-0.156$. This value is close to the prediction of the PSA, but it results from the attenuation of the signal by noise, which shows that a noisy circuit can appear to agree with the approximation without resolving the difference.

![Estimates of C3 in the primary case under readout error and two-qubit depolarization, with and without mitigation.](figuras/figura-varredura-ruido.svg)

_Figure 2 - Estimates of $C^{(3)}_{012}$ in the primary case ($N=4$, $\lambda=3$, $\tau=2$) with the 12-step circuit and $M=327{,}680$ measurements per method. (a) Without gate noise, as a function of the readout error. (b) With a readout error of 0.03, as a function of the two-qubit depolarization. The bars are 95% intervals widened by the Trotter error, the solid line is the exact value with the $\pm0.01$ margin dotted, and the dashed line is the PSA._

The depth of the circuits explains the results of Table 7, in which the four estimates lay between $-0.0003$ and $0.0064$, with or without mitigation. In Aer, the 112 steps total 4,032 CNOTs, and an audit of the counts showed that the density matrix before readout was within $8\times10^{-11}$ of the maximally mixed state, so that the gate noise erased the signal. On the hardware, the 14-step circuit has 672 CZ gates, more than the 648 CNOTs of the 12-step circuit of Figure 2, whose sweep already fails at $p=10^{-4}$ to resolve the cumulant at $\tau=2$. The synthetic depolarizing parameter is not directly the physical CNOT or CZ infidelity. The execution on `ibm_kingston` completed twenty blocks and eighty jobs, with 655,360 measurements including calibrations, in 72.87 minutes. For this reason, the hardware experiment was redone with the short circuit of $\tau=1.5$.

_Table 7 - Estimates of $C^{(3)}$ in the primary case ($\tau=2$) and 95% interval of the circuit-minus-exact difference, widened by the Trotter error. Each method receives $M=327{,}680$ measurements, and the calibration is part of the mitigated budget. The two-qubit gates are CNOTs in Aer and CZ on the processor. The exact value is $-0.316$, and that of the PSA, $-0.151$._

| Environment | Steps | Two-qubit gates | Method    |  Estimate | 95% CI of the difference |
| ----------- | ----: | --------------: | --------- | --------: | ------------------------ |
| Aer         |   112 |           4,032 | Raw       | $-0.0003$ | $[0.312,\ 0.319]$        |
| Aer         |   112 |           4,032 | Mitigated |  $0.0013$ | $[0.312,\ 0.322]$        |
| IBM         |    14 |             672 | Raw       |  $0.0058$ | $[0.318,\ 0.326]$        |
| IBM         |    14 |             672 | Mitigated |  $0.0064$ | $[0.317,\ 0.327]$        |

With the short circuit, the processor preserved a measurable signal. The IBM estimate was $C^{(3)}=-0.097$, against $-0.159$ for the exact result and $-0.054$ for the PSA, so that the circuit recovered 61% of the cumulant and the approximation, 34%. The absolute error of the circuit was 0.062, and that of the PSA, 0.104, with $\Delta=-0.043$ $[-0.046,\ -0.039]$. The interval of the circuit-minus-PSA difference also excluded zero. A simulation of the same circuit in Aer, with the calibrated noise model of the processor and the same number of measurements, predicted $C^{(3)}=-0.081$, close to the measured value. The interval of the circuit-minus-exact difference, $[0.058,\ 0.065]$, however, lay outside the $\pm0.01$ margin, and the criterion of Equation (9) was not satisfied. The hardware therefore distinguished the prediction of the PSA and was closer to the exact result than it, but the total attenuation of about 40% still prevents recovering the exact value in this execution. The simulations point to the relevance of gate noise, without attributing the whole loss exclusively to the CZ gates. A noise sweep in Aer on the executed circuit itself, with 100 synthetic measurement campaigns per condition, placed the two-qubit depolarization threshold between $4.8\times10^{-4}$ and $5.6\times10^{-4}$ for both methods, numerically above the levels approved in the 648-CNOT circuit. The difference does not isolate the effect of depth, because the physical points, the gates, and the criteria differ. In this sweep, without gate noise and with a readout error of 0.03, the mitigated method satisfied the criterion in 97 of 100 campaigns and the raw method in none, which reinforces the benefit of readout mitigation in this model, with the additional criterion described in the metrics section.

The points with six and eight qubits also preserved measurable signals (Table 8). In the confirmation, the hardware estimated $C^{(3)}=0.184$ for $N=6$, against $0.415$ for the exact result and $0.137$ for the PSA, and $C^{(3)}=-0.028$ for $N=8$, against $-0.131$ for the exact result and $0.050$ for the PSA. For $N=8$, the PSA predicted the wrong sign of the cumulant, and the hardware recovered the correct sign. The four comparisons of absolute error, against the PSA and against the prediction $C^{(3)}=0$ at each size, favored the hardware with simultaneous 98.75% intervals, and the pilots of five jobs already indicated the same result. Even so, the hardware recovered only 44% of the exact cumulant for $N=6$ and 21% for $N=8$, and no point lay within the $\pm0.01$ margin. For $N=8$, the Trotter error itself, of $1.3\times10^{-2}$, already exceeds this margin. The averages per calibration window ranged from 0.167 to 0.195 for $N=6$ and from $-0.045$ to $-0.012$ for $N=8$, a drift that the interval obtained by resampling the jobs includes but does not model. A simulation in Aer with the calibrated noise model of the processor predicted $0.172$ and $-0.012$ for the pilots, in the same direction as the measured values. Because the points differ in geometry, initial state, interaction, and time, the differences between sizes do not isolate the effect of $N$.

_Table 8 - Executions on `ibm_kingston` with circuits of two Trotter steps. $\Delta$ is the difference between the absolute errors of the hardware and of the PSA, and negative values indicate the hardware closer to the exact result. The intervals are 95% in the pilots and in the $N=4$ case, and simultaneous 98.75% in the confirmation with six and eight qubits. The PSA uses all initial conditions._

| Execution    | $N$ |  CZ | Jobs × measurements | Hardware |    Exact |      PSA | $\Delta$                        |
| ------------ | --: | --: | ------------------: | -------: | -------: | -------: | ------------------------------- |
| Confirmation |   4 |  78 |         20 × 16,384 | $-0.097$ | $-0.159$ | $-0.054$ | $-0.043$ $[-0.046,\ -0.039]$    |
| Pilot        |   6 | 204 |           5 × 4,096 |  $0.195$ |  $0.415$ |  $0.137$ | $-0.058$ $[-0.074,\ -0.043]$    |
| Pilot        |   8 | 429 |           5 × 4,096 | $-0.022$ | $-0.131$ |  $0.050$ | $-0.073$ $[-0.081,\ -0.065]$    |
| Confirmation |   6 | 204 |          20 × 4,096 |  $0.184$ |  $0.415$ |  $0.137$ | $-0.047$ $[-0.056,\ -0.037]$    |
| Confirmation |   8 | 429 |          20 × 4,096 | $-0.028$ | $-0.131$ |  $0.050$ | $-0.078$ $[-0.088,\ -0.068]$    |

## Discussion

### Comparison with related works

Table 9 compares the methods, the quantities, and the test conditions of this work with the two closest studies, Lacroix et al. (2024) for the PSA and Illa and Savage (2023) for the measurement of cumulants on hardware.

_Table 9 - Test conditions of this work and of the closest studies. Source: prepared by the authors, based on the works cited._

| Aspect        | Lacroix et al. (2024)    | Illa and Savage (2023)                | This work                                     |
| ------------- | ------------------------ | ------------------------------------- | --------------------------------------------- |
| Methods       | Exact, PSA               | Exact, circuit                        | Exact, mean field, PSA, circuit               |
| $N$           | 4, 8, and 12             | Up to 12                              | 4 to 16 (classical); 4 to 8 (hardware)        |
| Initial state | Half in each flavor      | Half in each flavor                   | Half in each flavor                           |
| Correlations  | Collective $C_{ZZ}$      | $C^{(2)}$ and $C^{(3)}$               | $C^{(2)}$ per pair and $C^{(3)}$ per triple   |
| Approximation | PSA compared with exact  | None                                  | PSA compared with exact and with the circuits |
| Measurements  | Not applicable           | 240 (processor) and 1,200 (emulator)  | 81,920 to 327,680 per circuit                 |
| Platform      | Classical                | Trapped ions                          | Classical, Aer, and `ibm_kingston`            |

In the arrangement of Lacroix et al. (2024), the PSA reproduced the collective correlation $C_{ZZ}$ well, whereas the results of this work indicate high errors in pairs and triples. The two observations are compatible. The published quantity $C_{ZZ}$ includes local terms $i=j$; here, the sum $K_{ZZ}=\sum_{i<j}C^{(2)}_{ij}$ considers only distinct pairs. Calculated on the same data as Table 6, this sum had a normalized error between 0.06 and 0.37 and lay below the pair-by-pair error $R_2$ in 21 of the 25 configurations. In the primary case, this error was 0.17, against $R_2=0.42$ and $R_3=0.95$. The deviations of the individual pairs partly cancel in the sum, so that a collective quantity can be well reproduced even when the correlations of each pair and of each triple are not. The overdamping of the flavor averages reported by these authors also appears here, as the increase of the error of $P_e$ with the interaction, which reaches $R_1$ between 0.53 and 1.01 at $\lambda=10$. The main difference lies in the quantity compared. The earlier validation did not examine three-body cumulants, in which the PSA departs most from exact evolution, or the dependence on $\lambda$.

Illa and Savage (2023) used the same definition of connected cumulant and the same initial state, but most of the three-body cumulants measured were compatible with zero. The results of this work illustrate the relevance of the measurement budget, without identifying a single cause for the uncertainties of that study. In the short circuit, the 95% interval of the difference between IBM and the exact result had a half-width of 0.0035 with 327,680 measurements, which corresponds to a standard error of about 0.0018. By the $M^{-1/2}$ dependence observed in Figure 1, the same circuit, hypothetically keeping its distribution and using 240 measurements, would have a standard error close to 0.07, comparable to the exact cumulant itself, of $-0.159$. With the enlarged budget, the hardware resolved a nonzero cumulant and also distinguished it from the prediction of the PSA. With 81,920 measurements, the circuits of six and eight qubits also resolved nonzero cumulants, including the negative sign for $N=8$, which the PSA misses. The comparison with an approximation, absent from that study, is also added. The attenuation observed, of about 40% for $N=4$ and of 56% and 79% for $N=6$ and $N=8$, shows, however, that increasing the budget is not enough and that, beyond statistics, gate noise limits the recovery of the exact value.

### Analysis of the hypotheses and objectives

The nominal intervals indicated a larger normalized error of the triples than of the flavor probabilities in the 25 configurations, and than of the pairs in 22 of them. The control grid without Monte Carlo error supported the larger normalized error of the triples in all 15 configurations of that window. The error of the triples grew with the interaction in systems of four to eight neutrinos in the window $0\leq\tau\leq10$, but not at the initial times, $\tau\leq3$, so that this part of H1 depends on the time window. In the primary case, with $N=4$, $\lambda=3$, and $\tau=2$, the approximation recovered 48% of the exact triple cumulant, a deviation far above the sampling and integration uncertainties. In systems of twelve and sixteen neutrinos, the error of the triples remained larger but did not grow monotonically with the interaction. At strong coupling, the PSA also lost accuracy in the flavor probabilities, which reduces the advantage of the one-particle observables over the triples. At weak coupling, the cumulants are small and the Monte Carlo noise of the PSA itself must be subtracted, or it produces spurious differences between triples and pairs.

Ideal quantum circuits distinguished this deviation with room to spare, with an error that decreases as $m^{-1/2}$ and lies below $2\times10^{-3}$ with 16,384 measurements per block. With noise, readout mitigation raised the tolerable readout error from less than 0.5% to 3%, which supports H2 for this type of noise. For gate noise, neither method tolerated depolarization above $3\times10^{-5}$ per two-qubit gate in the 648-CNOT circuit and under the synthetic channel adopted. This explains the estimates close to zero obtained on `ibm_kingston` with the original circuit and shows that, with realistic gate noise, the attenuation can bring the circuit to values close to those of the PSA without resolving the difference. With a redesigned circuit of 78 CZ gates, the processor recovered 61% of the exact cumulant and was closer to it than the PSA, which recovers 34%, but still outside the required margin. At two points with six and eight qubits and two beams, the hardware also erred less than the PSA and than the prediction $C^{(3)}=0$, and with eight qubits it recovered the sign of the cumulant that the PSA inverts, but it recovered only 44% and 21% of the exact value. At the points examined, the hardware therefore distinguishes the prediction of the PSA in short circuits, without yet serving as a quantitative reference for the triples.

### Limitations

The conclusions are restricted to a two-flavor model, to initial states with half of the neutrinos in each flavor, and to the $zzz$ component of the cumulants. The classical grid uses uniform coupling. The hardware points were chosen by prior calculations, differ from one another in several parameters, and constitute neither a scaling study in $N$ nor a demonstration of computational advantage, since exact evolution is still feasible at these sizes.

The intervals of the sampled grid are pointwise, and their coverage was not demonstrated for the whole grid. The archived validation of the original estimator found undercoverage in the weak regime; it does not automatically validate the corrected estimator. For this reason, the count of positive intervals is descriptive, and the complete enumeration supports the comparison only in the regimes in which it was calculated. The IBM executions without a comparison between raw and mitigated arms do not constitute a test of H2 on the device.

## Conclusion

In the configurations examined, the PSA showed a larger normalized error in the triples than in the flavor probabilities and, in most cases, than in the pairs. Quantum circuits distinguished this deviation when the gate noise was small or the circuit was short, but they did not recover the exact value on current hardware.

The objectives of comparing the orders of the observables and assessing interaction, measurements, and noise were met in the configurations defined. The trend with the interaction depends on the time window, and the benefit of mitigation is restricted to the readout mechanism assessed.

## Future work

Future work can extend the comparison to non-uniform angular couplings and to three flavors, increase the number of trajectories at weak coupling, and combine readout mitigation with zero-noise extrapolation, to assess whether the hardware execution reaches the required resolution margin.

## Code and data

The code, the protocols, and the derived data are at <https://github.com/leonardovbf/correlacoes-tres-neutrinos>. The numerical engine (exact, mean field, PSA, and circuits) is in `src/neutrinos/`, the protocols of each phase in `configs/protocols/artigo_v1/`, and the statistical analysis in `src/neutrinos/study_analysis.py`. The results of this article are reproduced, in this order, by `scripts/grade_psa.py gerar`, `scripts/grade_psa.py analisar`, `scripts/grade_psa.py ordens`, and `scripts/grade_psa.py coletivo` (H1 grid and comparison with the collective correlation), `scripts/varredura_ruido.py` (H2), `figuras/dados_orcamento.py` (measurement budget), and by `figuras/gerar_tabelas.py`, `figuras/figura_orcamento.py`, and `figuras/figura_ruido.py` (tables and figures). The reference scientific environment uses CPython 3.14.3, NumPy 2.4.3, SciPy 1.17.1, Qiskit 2.5.2, Qiskit Aer 0.18.2, Qiskit IBM Runtime 0.51.0, and Matplotlib 3.10.8, with the versions pinned in `requirements-research.lock`. All seeds are fixed, and the reproduction of the ideal measurements coincides with the original values in all 45 configurations. The raw counts, the compiled circuits, and the calibrations of the hardware executions of November 7 to 10 are in `analysis/campaigns/`, in the packages `20261108-resultados-ibm` (confirmation with four qubits and pilots), `20261108-aer-ibm-pareado` (simulation with calibrated noise), and `20261110-hardware-confirmation` (confirmation with six and eight qubits), with SHA-256 hashes of each file. The counts of the short circuit are also in `dados/ibm/circuito_curto_n4.json`, and `scripts/run_feedback_hardware.py verify` recalculates the confirmation with six and eight qubits from the counts, without access to IBM. The control grid with $\tau\leq3$ and the noise sweep on the executed circuit are summarized in `analysis/campaigns/20261109-feedback-v4/`. The counts of the 80 jobs of the first execution are also preserved in the file `existing_ibm_jobs.json` of the ZIPs of `20261109-feedback-v4`, which gathers 130 historical jobs. After the extraction described in the package, `analysis/feedback_delivery.py verify` verifies the reanalysis without access to IBM. The PSA trajectory blocks are regenerated deterministically by the scripts above.

## References

Abi, B. et al. (2020). Deep Underground Neutrino Experiment (DUNE), Far Detector Technical Design Report, Volume II: DUNE Physics. Technical Report FERMILAB-PUB-20-025-ND, DUNE Collaboration. <https://arxiv.org/abs/2002.03005>.

Akaho, R., Nagakura, H., Iwakami, W., Furusawa, S., Harada, A., Okawa, H., Matsufuru, H., Sumiyoshi, K., and Yamada, S. (2026). Bifurcated Impact of Neutrino Fast Flavor Conversion on Core-Collapse Supernovae Informed by Multiangle Neutrino Radiation Hydrodynamics. _Physical Review Letters_, 136(19):191002. <https://doi.org/10.1103/fksy-1jtw>.

Amitrano, V., Roggero, A., Luchi, P., Turro, F., Vespucci, L., and Pederiva, F. (2023). Trapped-ion quantum simulation of collective neutrino oscillations. _Physical Review D_, 107(2):023007. <https://doi.org/10.1103/PhysRevD.107.023007>.

Balantekin, A. B. and Pehlivan, Y. (2007). Neutrino–neutrino interactions and flavour mixing in dense matter. _Journal of Physics G: Nuclear and Particle Physics_, 34(1):47--65. <https://doi.org/10.1088/0954-3899/34/1/004>.

Baum, S., Capozzi, F., and Horiuchi, S. (2022). Rocks, water, and noble liquids: Unfolding the flavor contents of supernova neutrinos. _Physical Review D_, 106(12):123008. <https://doi.org/10.1103/PhysRevD.106.123008>.

Bravyi, S., Sheldon, S., Kandala, A., Mckay, D. C., and Gambetta, J. M. (2021). Mitigating measurement errors in multiqubit experiments. _Physical Review A_, 103(4):042605. <https://doi.org/10.1103/PhysRevA.103.042605>.

Cai, Z., Babbush, R., Benjamin, S. C., Endo, S., Huggins, W. J., Li, Y., McClean, J. R., and O'Brien, T. E. (2023). Quantum error mitigation. _Reviews of Modern Physics_, 95(4):045005. <https://doi.org/10.1103/RevModPhys.95.045005>.

Cervia, M. J., Patwardhan, A. V., Balantekin, A. B., Coppersmith, S. N., and Johnson, C. W. (2019). Entanglement and collective flavor oscillations in a dense neutrino gas. _Physical Review D_, 100(8):083001. <https://doi.org/10.1103/PhysRevD.100.083001>.

Childs, A. M., Su, Y., Tran, M. C., Wiebe, N., and Zhu, S. (2021). Theory of Trotter Error with Commutator Scaling. _Physical Review X_, 11(1):011020. <https://doi.org/10.1103/PhysRevX.11.011020>.

Cowan, J. J., Sneden, C., Lawler, J. E., Aprahamian, A., Wiescher, M., Langanke, K., Martínez-Pinedo, G., and Thielemann, F.-K. (2021). Origin of the heaviest elements: The rapid neutron-capture process. _Reviews of Modern Physics_, 93(1):015002. <https://doi.org/10.1103/RevModPhys.93.015002>.

de Correc, C., Lacroix, D., and Bertrand, C. (2026). Emulation of large-scale qubit registers with a phase-space approach. _APS Open Science_, 1:000017. <https://doi.org/10.1103/swn6-s387>.

Duan, H., Fuller, G. M., and Qian, Y.-Z. (2010). Collective Neutrino Oscillations. _Annual Review of Nuclear and Particle Science_, 60(1):569--594. <https://doi.org/10.1146/annurev.nucl.012809.104524>.

Hall, B., Roggero, A., Baroni, A., and Carlson, J. (2021). Simulation of collective neutrino oscillations on a quantum computer. _Physical Review D_, 104(6):063009. <https://doi.org/10.1103/PhysRevD.104.063009>.

Illa, M. and Savage, M. J. (2023). Multi-Neutrino Entanglement and Correlations in Dense Neutrino Systems. _Physical Review Letters_, 130:221003. <https://doi.org/10.1103/PhysRevLett.130.221003>.

Janka, H.-T. (2012). Explosion Mechanisms of Core-Collapse Supernovae. _Annual Review of Nuclear and Particle Science_, 62:407--451. <https://doi.org/10.1146/annurev-nucl-102711-094901>.

Kiss, O., Tavernelli, I., Tacchino, F., Lacroix, D., and Roggero, A. (2026). Neutrino thermalization via randomization on a quantum processor. _Communications Physics_, 9(1):282. <https://doi.org/10.1038/s42005-026-02697-2>.

Lacroix, D. and Ayik, S. (2014). Stochastic quantum dynamics beyond mean field. _The European Physical Journal A_, 50(6):95. <https://doi.org/10.1140/epja/i2014-14095-8>.

Lacroix, D., Balantekin, A. B., Cervia, M. J., Patwardhan, A. V., and Siwach, P. (2022). Role of non-Gaussian quantum fluctuations in neutrino entanglement. _Physical Review D_, 106(12):123006. <https://doi.org/10.1103/PhysRevD.106.123006>.

Lacroix, D., Bauge, A., Yilmaz, B., Mangin-Brinet, M., Roggero, A., and Balantekin, A. B. (2024). Phase-space methods for neutrino oscillations: Extension to multibeams. _Physical Review D_, 110:103027. <https://doi.org/10.1103/PhysRevD.110.103027>.

Lloyd, S. (1996). Universal Quantum Simulators. _Science_, 273(5278):1073--1078. <https://doi.org/10.1126/science.273.5278.1073>.

Mangin-Brinet, M., Bauge, A., and Lacroix, D. (2026). Three-flavor neutrino oscillations using the phase space approach. _Physical Review D_, 113:036026. <https://doi.org/10.1103/yr2g-1g2g>.

Martin, J. D., Roggero, A., Duan, H., Carlson, J., and Cirigliano, V. (2022). Classical and quantum evolution in a simple coherent neutrino problem. _Physical Review D_, 105(8):083020. <https://doi.org/10.1103/PhysRevD.105.083020>.

Nagakura, H. (2023). Roles of Fast Neutrino-Flavor Conversion on the Neutrino-Heating Mechanism of Core-Collapse Supernova. _Physical Review Letters_, 130(21):211401. <https://doi.org/10.1103/PhysRevLett.130.211401>.

Nielsen, M. A. and Chuang, I. L. (2010). _Quantum Computation and Quantum Information: 10th Anniversary Edition_. Cambridge University Press, Cambridge. <https://doi.org/10.1017/CBO9780511976667>.

Pehlivan, Y., Balantekin, A. B., Kajino, T., and Yoshida, T. (2011). Invariants of collective neutrino oscillations. _Physical Review D_, 84(6):065008. <https://doi.org/10.1103/PhysRevD.84.065008>.

Preskill, J. (2018). Quantum Computing in the NISQ era and beyond. _Quantum_, 2:79. <https://doi.org/10.22331/q-2018-08-06-79>.

Riccio, M. and Balantekin, A. B. (2026). Improved Approximations for Collective Neutrino Oscillations. Preprint arXiv:2607.28619, version 2. <https://doi.org/10.48550/arXiv.2607.28619>.

Rrapaj, E. (2020). Exact solution of multiangle quantum many-body collective neutrino-flavor oscillations. _Physical Review C_, 101(6):065805. <https://doi.org/10.1103/PhysRevC.101.065805>.

Sarmah, P., Chakraborty, S., Medhi, A., Bose, D., and Devi, M. M. (2026). Neutrino mass ordering from the next Galactic supernova at DUNE, HK, and JUNO. Preprint arXiv:2606.06580. <https://arxiv.org/abs/2606.06580>.

Shalgar, S. and Tamborra, I. (2023). Do we have enough evidence to invalidate the mean-field approximation adopted to model collective neutrino oscillations? _Physical Review D_, 107(12):123004. <https://doi.org/10.1103/PhysRevD.107.123004>.

Vatan, F. and Williams, C. (2004). Optimal quantum circuits for general two-qubit gates. _Physical Review A_, 69(3):032315. <https://doi.org/10.1103/PhysRevA.69.032315>.

Vissani, F., Costantini, M. L., Fulgione, W., Ianni, A., and Pagliaroli, G. (2010). What is the issue with SN1987A neutrinos? Preprint arXiv:1008.4726. <https://arxiv.org/abs/1008.4726>.

Volpe, C., Väänänen, D., and Espinoza, C. (2013). Extended evolution equations for neutrino propagation in astrophysical and cosmological environments. _Physical Review D_, 87(11):113010. <https://doi.org/10.1103/PhysRevD.87.113010>.
