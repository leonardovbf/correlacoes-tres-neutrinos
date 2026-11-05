# Beyond mean field: can low-cost approximations capture neutrino correlations in supernovae?

_Além do campo médio: aproximações de baixo custo capturam as correlações entre neutrinos em supernovas?_

## Resumo

O sabor dos neutrinos emitidos em supernovas de colapso de núcleo pode influenciar a dinâmica da explosão e as condições de produção de elementos pesados. A descrição de sua evolução quântica de muitos corpos motiva o uso de aproximações, cuja precisão depende do regime investigado. Este projeto tem como objetivo delimitar o domínio de validade da aproximação de espaço de fase nas correlações conectadas de dois e três corpos e quantificar as condições necessárias para que circuitos quânticos resolvam seus desvios em relação à solução exata. Será estudado um modelo de dois sabores, com interações entre todos os pares e energias distintas. Serão comparadas a evolução exata, a de campo médio e a aproximação de espaço de fase para sistemas de quatro até cerca de dezesseis neutrinos, variando a razão entre intensidade de interação e frequência média de oscilação no vácuo de 0,1 a 10 e examinando janelas temporais e estados iniciais previamente definidos. A hipótese principal prevê maior erro normalizado nos cumulantes de três corpos do que nos de dois corpos, quando as referências permitirem normalização. Circuitos trotterizados em Qiskit para quatro a oito neutrinos serão usados para avaliar a resolução das discrepâncias identificadas, com referência clássica acessível nesses tamanhos. Será investigado se a mitigação amplia o limiar de ruído tolerável para essa distinção, mantendo o mesmo orçamento total de medições. Serão controladas as incertezas de amostragem, integração numérica e trotterização, com execução em hardware IBM condicionada à disponibilidade. Espera-se estabelecer os regimes de precisão da aproximação e os limites de resolução dos circuitos no modelo estudado.

**Palavras-chave:** Neutrinos. Oscilações coletivas. Correlações de três corpos. Computação quântica. Aproximação de espaço de fase.

## Abstract

The flavor of neutrinos emitted in core-collapse supernovae can influence explosion dynamics and the conditions for heavy-element production. Describing their quantum many-body evolution motivates the use of approximations whose accuracy depends on the regime investigated. This project aims to establish the range of validity of the phase-space approximation for connected two- and three-body correlations and quantify the conditions required for quantum circuits to resolve its deviations from exact evolution. A two-flavor model with all-to-all interactions and distinct energies will be studied. Exact, mean-field, and phase-space evolution will be compared for systems of four to approximately sixteen neutrinos, varying the ratio of interaction strength to mean vacuum oscillation frequency from 0.1 to 10 and examining predefined time windows and initial states. The main hypothesis predicts a larger normalized error for three-body than for two-body cumulants when the references permit normalization. Trotterized Qiskit circuits for four to eight neutrinos will be used to assess the resolution of the identified discrepancies, with a classical reference accessible at these sizes. The study will investigate whether mitigation increases the noise threshold tolerated for this distinction at the same total measurement budget. Sampling, numerical integration, and Trotterization uncertainties will be controlled, with execution on IBM hardware subject to availability. The expected contribution is to establish the approximation's accuracy regimes and the circuits' resolution limits within the model studied.

**Keywords:** Neutrinos. Collective oscillations. Three-body correlations. Quantum computing. Phase-space approximation.

## Introduction

### Astrophysical context and motivation

Stars with initial masses above approximately eight solar masses can undergo gravitational core collapse. In a typical scenario, an iron-rich core surrounded by nuclear-burning shells loses support, contracts to near-nuclear densities, and undergoes a bounce, generating a shock (JANKA, 2012; ABI et al., 2020).

The shock can stall through energy losses from nuclear dissociation and neutrino emission. Neutrino absorption and fluid motion can revive it during accretion, meaning matter falling onto the remnant. Stellar structure and accretion influence explosion or black-hole formation if the remnant exceeds the mass it can support (JANKA, 2012; Figure 1).

![Three panels show a contracting stellar core, neutrino heating behind the shock, and the possible outcomes of explosion or black-hole formation.](figuras/en/figure-1-core-collapse.png)

*Figure 1 - Stellar core collapse, not to scale. (a) Core contraction and bounce. (b) Stalled shock and neutrino heating around the proto-neutron star (PNS). (c) Explosion or black-hole formation, including after an explosion. Source: original illustration based on Janka (2012).*

Neutrinos are electrically neutral elementary particles that interact weakly with matter and can become temporarily trapped in the dense core. A typical supernova emits about $10^{58}$ neutrinos, with characteristic energies of $10\,\mathrm{MeV}$, over approximately ten seconds, carrying more than 99% of the gravitational energy released by the collapsed core (ABI et al., 2020).

During supernova SN 1987A, in the Large Magellanic Cloud, Kamiokande-II, IMB, and Baksan recorded a few dozen events associated with the neutrino burst, allowing the interior of the collapsing star to be probed (VISSANI et al., 2010).

The electron, muon, and tau flavors correspond to their respective charged leptons in weak interactions. Flavor states are superpositions of mass states, whose propagation phases change detection probabilities, producing oscillations. The discovery, recognized by the 2015 Nobel Prize in Physics, established nonzero masses. Here, the electron and effective nonelectron flavors are represented by the states of a qubit, the basic unit of quantum information (DUAN; FULLER; QIAN, 2010; NOBEL PRIZE, 2015).

Absorption of electron neutrinos on neutrons or electron antineutrinos on protons heats matter behind the shock and interconverts neutrons and protons. Nagakura (2023) found an approximately 40% reduction in this heating with flavor conversion in the spherically symmetric configuration studied. In multidimensional models, Akaho et al. (2026) observed effects that favored or hindered explosion, depending on the progenitor and accretion.

The neutron-to-proton composition also affects nucleosynthesis, or the formation of atomic nuclei. The r-process, rapid neutron capture, produces some elements heavier than iron in neutron-rich matter, as in neutron-star mergers and rare explosions (COWAN et al., 2021).

DUNE is particularly sensitive to electron neutrinos; Hyper-Kamiokande and JUNO have important electron-antineutrino channels, providing complementary information about supernovae (BAUM; CAPOZZI; HORIUCHI, 2022; SARMAH et al., 2026). Interpreting these signals requires predicting their flavors. Near the core, coherent interactions between neutrinos couple flavor evolution, generating collective oscillations and the many-body problem discussed next (DUAN; FULLER; QIAN, 2010).

### State of the art and research gap

The collective dynamics described above constitutes a quantum many-body problem in which correlations and entanglement can develop between neutrinos, with entanglement associated with the nonseparability of the joint quantum state. In the general two-flavor representation, a pure state of $N$ neutrinos has $2^N$ complex amplitudes. This growth limits exact evolution of large systems on classical computers when no specific symmetries or compression schemes are exploited ([DUAN; FULLER; QIAN, 2010](https://doi.org/10.1146/annurev.nucl.012809.104524); [CERVIA et al., 2019](https://doi.org/10.1103/PhysRevD.100.083001)).

One strategy to reduce this cost is the mean-field approximation, which replaces the effects of other particles with an effective field determined by their averages. By factorizing expectation values of operators acting on distinct particles, this description neglects connected correlations and, for initially factorized states, does not track the generation of entanglement between neutrinos. [Cervia et al. (2019)](https://doi.org/10.1103/PhysRevD.100.083001) related differences between exact and mean-field evolution to the development of entanglement, with a dependence on initial conditions. In a three-flavor model, [Mangin-Brinet, Bauge, and Lacroix (2026)](https://doi.org/10.1103/yr2g-1g2g) also observed short-time deviations in the configurations examined. The validity of the approximation must therefore be assessed in terms of the model, initial conditions, and dynamical regime.

The phase-space approximation (PSA) seeks to incorporate effects beyond mean field through an ensemble of independent trajectories. Initial conditions are sampled to reproduce selected quantum moments, and each trajectory evolves according to mean-field equations; observables are estimated by statistical averages over the ensemble. [Lacroix et al. (2022)](https://doi.org/10.1103/PhysRevD.106.123006) obtained good agreement with mean values and entropies of one- and two-neutrino reduced states, calculated from their respective density matrices, in a two-beam model, although they did not reproduce long-time oscillations of fluctuations. The extension to multiple beams also compared collective two-body correlations through the covariance-based observable $C_{ZZ}$. This collective validation is not equivalent to assessing every pair individually and does not establish the accuracy of third-order cumulants ([LACROIX et al., 2024](https://doi.org/10.1103/PhysRevD.110.103027)). The extension to three flavors was subsequently compared with exact solutions for up to eight neutrinos ([MANGIN-BRINET; BAUGE; LACROIX, 2026](https://doi.org/10.1103/yr2g-1g2g)).

Another approach beyond mean field truncates the Bogoliubov–Born–Green–Kirkwood–Yvon (BBGKY) hierarchy, which relates the evolution of one-particle observables to higher-order correlations. In the preprint by [Riccio and Balantekin (2026)](https://arxiv.org/abs/2607.28619), the second-order closure retains pair contributions and sets connected three-body cumulants to zero to close the equations. This condition does not necessarily set the expectation value of a product of three operators to zero, because contributions constructed from individual means and pairs remain. PSA incorporates higher moments without imposing the same closure; its accuracy for third-order cumulants must be examined directly ([LACROIX et al., 2022](https://doi.org/10.1103/PhysRevD.106.123006)).

Quantum simulations offer a complementary route to investigate these correlations. [Hall et al. (2021)](https://doi.org/10.1103/PhysRevD.104.063009) demonstrated simulations of small neutrino systems on noisy devices, using error mitigation, namely techniques to reduce the effects of noise on observable estimates, to extract entanglement measures. [Illa and Savage (2023)](https://doi.org/10.1103/PhysRevLett.130.221003) investigated systems of up to twelve neutrinos on the Quantinuum H1-1 trapped-ion processor, including two- and three-body correlations and multipartite entanglement indicators. At a larger scale, [Kiss et al. (2026)](https://doi.org/10.1038/s42005-026-02697-2) studied thermalization with random circuits on IBM processors using more than one hundred qubits. Their performance was assessed through thermalization observables; the fidelity of specific cumulants during evolution requires separate validation.

The relevance of third-order cumulants also follows from the evolution hierarchy. For a Hamiltonian with pair interactions, the dynamics of one-particle observables depends on two-body correlations, whose equations couple to third-order moments ([LACROIX et al., 2024](https://doi.org/10.1103/PhysRevD.110.103027); [RICCIO; BALANTEKIN, 2026](https://arxiv.org/abs/2607.28619)). Deviations in the description of these contributions may therefore affect lower-order observables during evolution. This coupling motivates investigating triples, although the analysis of a single flavor component does not establish the origin of all deviations in probabilities.

Within the literature examined, no systematic comparison of PSA three-body cumulants with exact evolution was identified that controls system size, interaction strength, and computational and measurement uncertainties. Agreement in flavor averages, collective pair correlations, or reduced entropies does not guarantee accurate third-order cumulants. Addressing this gap requires establishing the approximation's validity regimes and separating its error from finite sampling, time discretization, and noise.

For the systems of four to eight neutrinos considered for the circuits, exact evolution is classically accessible and will provide a controlled reference. The quantum stage seeks to determine the precision and resources required to resolve discrepancies between PSA and this reference. Trotterization approximates the full evolution through a sequence of operations associated with the Hamiltonian terms over small time steps. The availability of exact calculations allows the effects of this discretization, noise, and measurement counts to be assessed separately; demonstrating a computational advantage at these sizes is not an objective. The astrophysical context motivates the model, but conclusions will remain restricted to the simplified configurations investigated.

### Research question, objective, and hypotheses

The central question is: in which regimes of interaction strength, system size, and evolution time, for the initial states considered, does PSA reproduce connected two- and three-body cumulants within predefined tolerances? Additionally, in regimes where its deviations from exact evolution are resolved, which noise conditions and measurement budgets allow quantum circuits to distinguish these predictions?

The general objective is to establish PSA's range of validity and quantify the conditions under which quantum circuits can resolve its deviations. Exact, mean-field, and PSA evolution will therefore be compared in a two-flavor model with distinct energies and interactions between all pairs. Python will be used for systems of four to approximately sixteen neutrinos and Qiskit for circuits of four to eight neutrinos, varying $\mu/\bar{\omega}$ from 0.1 to 10. Here, $\mu$ denotes the neutrino–neutrino interaction scale and $\bar{\omega}$ the mean vacuum oscillation frequency. The assessment will cover flavor probabilities, pair and triple cumulants, numerical convergence, and sampling uncertainties, followed by circuit comparisons with and without mitigation.

PSA sampling is constructed to reproduce selected initial moments, and evolution through mean-field trajectories does not guarantee the reproduction of connected third-order cumulants. These cumulants result from subtracting individual and pair contributions from the three-body moment; deviations in these contributions may produce large relative errors when the connected part is small, even if numerically resolved. The limitations in reproducing long-time fluctuation oscillations observed by Lacroix et al. (2022) also motivate examining their accuracy over different time windows. These arguments guide hypothesis **H1**: for the initial states and time windows specified in advance, PSA's normalized error for three-body cumulants is systematically larger than that for two-body cumulants when the references permit normalization. Individual flavor probabilities will remain an additional performance reference.

_Falsification criterion for H1: the comparison across scenarios, using the aggregation rule and difference margin specified in the protocol, establishes that the error for triples does not exceed that for pairs by the predicted margin. If uncertainties prevent these possibilities from being distinguished, the result will be considered inconclusive._

The dependence of error on interaction strength will be examined as a secondary analysis. Increasing $\mu$ increases the coefficients of the interaction terms coupling the hierarchy's orders, motivating an investigation of growing deviations. This argument does not, however, establish monotonic growth of normalized error, which also depends on the initial state, evolution time, and reference amplitude. The trend will be assessed within the defined regimes, without being assumed throughout the interval studied.

The quantum stage will examine hypothesis **H2**: for the scenarios selected in advance, the adopted mitigation technique increases the noise threshold at which three-body cumulants allow PSA to be distinguished from exact evolution, at a fixed total measurement budget. This hypothesis compares performance for a specified noise model and mitigation procedure, without assuming that mitigation is necessary under all conditions.

_Falsification criterion for H2: the comparison establishes that the mitigated threshold does not exceed the unmitigated threshold by the margin specified in the protocol, at the same total measurement budget. If the difference between thresholds cannot be determined with the required precision, the result will be considered inconclusive._

Initial states, time windows, tolerances, the noise model, the mitigation technique, and statistical criteria will be recorded before confirmatory comparisons. The strategy below organizes these definitions and the control of error sources.

## Proposed evaluation strategy

### Definition of regimes

Scenarios will be defined by system size $N$, the ratio $\mu/\bar{\omega}$, initial states, frequencies, and pair couplings. The frequency distribution, flavor convention, and Hamiltonian normalization will be stated explicitly, allowing a published case to be reproduced before parameter scans. The parameter grid, particle sets, and time windows will be recorded in advance; changes motivated by an exploratory stage will be identified before confirmatory assessment.

Comparisons across interaction strengths will use common windows of dimensionless time $\bar{\omega}t$. Since the scale $\mu t$ varies in this comparison, it will also be reported to distinguish changes in the interaction regime from differences in the number of dynamical timescales elapsed. PSA's range of validity will be determined by the error tolerances and uncertainties established in the protocol, with results separated by time window and initial state.

### Observables and connected correlations

To make the meaning of correlations explicit, consider the flavor operator $Z_i = |\nu_e\rangle_i\langle\nu_e| - |\nu_x\rangle_i\langle\nu_x|$, equivalent to the Pauli matrix $\sigma_z$ on qubit $i$, where $\nu_x$ is the effective nonelectron flavor. Its mean is $m_i(t)=\langle Z_i\rangle_t$, and the electron-flavor probability is $P_{e,i}(t)=[1+m_i(t)]/2$. For distinct particles, these operators commute, and second- and third-order cumulants are defined as

$$
C^{(2)}_{ij}(t)=\langle Z_i Z_j\rangle_t-m_i(t)m_j(t)
$$

and

$$
\begin{aligned}
C^{(3)}_{ijk}(t)={}&\langle Z_i Z_j Z_k\rangle_t-m_i(t)m_j(t)m_k(t)\\
&-C^{(2)}_{ij}(t)m_k(t)-C^{(2)}_{ik}(t)m_j(t)-C^{(2)}_{jk}(t)m_i(t).
\end{aligned}
$$

Figure 2 represents this decomposition: a three-particle moment combines products of means, pair contributions, and a connected three-body term. Neglecting $C^{(3)}_{ijk}$ in a closure is therefore not equivalent to neglecting $\langle Z_i Z_j Z_k\rangle$. This identity is a particular case of the cumulant expansion discussed by Riccio and Balantekin (2026). The main analysis will consider the $Z$, $ZZ$, and $ZZZ$ components, with particle sets specified in the protocol. Conclusions about their accuracy will not automatically be extended to other Pauli components.

![Decomposition of a moment of three flavor operators into individual means, three pair-times-mean terms, and the connected third-order cumulant.](figuras/en/figure-2-connected-correlations.png)

*Figure 2 - Decomposition of the moment $\langle Z_iZ_jZ_k\rangle$. (a) Product of individual means $m_i m_j m_k$. (b) Three contributions consisting of a pair cumulant times the mean of the remaining particle. (c) Connected cumulant $C^{(3)}_{ijk}$, highlighted as the part remaining after subtracting the preceding terms. Circles identify distinct particles $i$, $j$, and $k$; one link denotes a pair contribution, and the three-linked diamond denotes the triple cumulant without representing another particle. This statistical notation represents neither additional Hamiltonian interactions nor an entanglement certificate. All terms are evaluated at the same time. Source: original illustration based on the cumulant expansion of Riccio and Balantekin (2026).*

### Comparison criteria

The same observables, flavor basis, and normalization will be used in every method. Connected correlations will be described by cumulants of operators acting on distinct particles; a nonzero cumulant alone does not certify genuine entanglement. Absolute error will be reported over time and summarized by the root mean square of deviations. Normalized error will be the ratio of this measure to the root mean square of the exact reference, calculated over the same time grid and set of observables. The minimum signal threshold for this normalization will be fixed in advance according to numerical precision and the scale of interest. Below this threshold, absolute error will be reported, and the case will be excluded from H1's normalized-error comparison.

H1 will be assessed by comparing normalized errors for pairs and triples within each eligible scenario over the same time window. The protocol will specify the aggregation rule across scenarios and the relevant difference margin, preventing an isolated case from determining the conclusion. Sampling convergence will be examined using different trajectory counts and independent random seeds to separate approximation error from statistical fluctuations. Flavor probabilities and absolute errors will complement this comparison.

In quantum assessments, a difference will be considered resolved when the confidence interval for the deviation between the circuit estimate and the exact reference lies within a predefined equivalence margin, and the interval for the difference between the circuit and PSA excludes zero. Uncertainties in both methods and reference tolerances will be considered. The confidence level, minimum success frequency across independent repetitions, and treatment of comparisons across times and observables will be specified in the protocol. Finite sampling, numerical integration, Trotterization, and noise will be assessed separately.

### Method comparison and error control

Figure 3 organizes the proposed protocol. For each system size, interaction strength, and initial state, the same Hamiltonian and observable definitions will be used for exact, mean-field, PSA, and circuit evolution. Initial conditions sampled by PSA must reproduce the moments prescribed by the method for the chosen physical state. Systems of four to eight neutrinos will be shared by all four methods; classical comparisons will extend to approximately sixteen neutrinos. This organization combines the systematic exact-reference comparisons of Lacroix et al. (2024) with the distinction between exact evolution, Trotterization, and measurements used by Hall et al. (2021) and Illa and Savage (2023).

![Three-column protocol showing a shared model with all-to-all interactions, four evolution methods, and observables compared against exact evolution, with emphasis on the three-body cumulant.](figuras/en/figure-3-comparison-protocol.png)

*Figure 3 - Proposed comparison protocol. (a) A Hamiltonian $H$ and initial state $|\Psi_0\rangle$ shared by the methods, in the two-flavor model with distinct energies and $\mu/\bar{\omega}$ between 0.1 and 10. The four-node network illustrates interactions between all pairs; it represents neither processor connectivity nor a limit on system size. (b) Exact, mean-field, and PSA evolution for four to approximately sixteen neutrinos; circuits for the subset of four to eight, under ideal and noisy conditions. (c) Comparison of probabilities and cumulants against exact evolution, highlighting $C^{(3)}_{ijk}$. The bottom row groups integration, sampling, Trotter, measurement, and noise controls. Comparisons with and without mitigation will use the same total measurement budget; hardware execution will depend on availability. Source: original illustration informed by the comparisons of Lacroix et al. (2024), Hall et al. (2021), and Illa and Savage (2023).*

Before interpreting physical differences, convergence will be checked by refining time integration, increasing the number of PSA trajectories, and reducing the Trotter step in ideal simulation. Noisy assessments will follow this validation. Cumulant uncertainties must account for the fact that means and products may be estimated from the same measurements or trajectories, preserving their covariances during error propagation or resampling. Each configuration will record model parameters, initial state, time grid and interval, numerical tolerances, random seeds and trajectory counts, Trotter steps, noise model, measurement counts, and mitigation procedure.

### Noise threshold and measurement budget

Quantum-stage scenarios will be selected from cases with four to eight neutrinos in which the difference between PSA and exact evolution is resolved after classical controls. The selection rule, triples, and times will be fixed before noisy runs, without subsequently selecting only favorable results. Trotter error will be reduced to a tolerance consistent with the discrepancy to be measured.

For each scenario, a family of noise channels parametrized by $p$ will be adopted, with its interpretation specified. The reference circuit, compilation rule, and total measurement budget $M$ will be held fixed, including measurements used in mitigation calibrations and auxiliary circuits. For each procedure, $p_{\max}(M)$ will denote the largest assessed noise level satisfying the resolution criterion. H2 will be examined through the difference between $p_{\max}^{\mathrm{mitigated}}(M)$ and $p_{\max}^{\mathrm{unmitigated}}(M)$, accounting for scan resolution and statistical uncertainties.

If the transition between resolution and lack of resolution is not observed within the assessed interval, bounds on the threshold will be reported. If behavior is nonmonotonic, resolution regions in the $(p,M)$ plane will be presented, without assuming that every noise level below the largest successful value also satisfies the criterion. Conclusions about mitigation will remain restricted to the procedure, noise model, and scenarios examined; execution on IBM hardware, when available, will be reported with its operating conditions.

### Presentation of results

Results will be presented in separate panels for probabilities, pair cumulants, and triple cumulants. Line and symbol meanings will remain consistent: exact evolution as a solid black line, mean field as a dotted gray line, PSA as a dashed blue line, and circuit estimates as symbols with uncertainty bars. Circles and squares will distinguish unmitigated and mitigated estimates without relying on color alone. Captions will specify the initial state, $N$, $\mu/\bar{\omega}$, dimensionless time $\bar{\omega}t$, sampling resources, and the statistical meaning of the bars. Deviation and normalized-error panels will complement the curves according to the established criteria; error tables or maps will delineate validity regimes by system size, interaction strength, initial state, and time window. The quantum stage will present thresholds or resolution regions as functions of noise and total measurement budget, with and without mitigation, including inconclusive cases and limits not reached by the scan. Gate diagrams will show the implemented circuit and its Trotter order.

## Use of generative artificial intelligence

Generative artificial intelligence assistance was used to support writing revision, translation, and the production of code for the conceptual diagrams.

## References

ABI, B. et al. **Deep Underground Neutrino Experiment (DUNE), Far Detector Technical Design Report, Volume II: DUNE Physics**. Technical report, 2020. arXiv:2002.03005. Available at: https://arxiv.org/abs/2002.03005. Accessed: 23 Oct. 2026.

AKAHO, R. et al. Bifurcated impact of neutrino fast flavor conversion on core-collapse supernovae informed by multiangle neutrino radiation hydrodynamics. **Physical Review Letters**, v. 136, art. 191002, 2026. DOI: [10.1103/fksy-1jtw](https://doi.org/10.1103/fksy-1jtw).

BAUM, S.; CAPOZZI, F.; HORIUCHI, S. Rocks, water, and noble liquids: unfolding the flavor contents of supernova neutrinos. **Physical Review D**, v. 106, art. 123008, 2022. DOI: [10.1103/PhysRevD.106.123008](https://doi.org/10.1103/PhysRevD.106.123008).

CERVIA, M. J.; PATWARDHAN, A. V.; BALANTEKIN, A. B.; COPPERSMITH, S. N.; JOHNSON, C. W. Entanglement and collective flavor oscillations in a dense neutrino gas. **Physical Review D**, v. 100, art. 083001, 2019. DOI: [10.1103/PhysRevD.100.083001](https://doi.org/10.1103/PhysRevD.100.083001).

COWAN, J. J. et al. Origin of the heaviest elements: the rapid neutron-capture process. **Reviews of Modern Physics**, v. 93, art. 015002, 2021. DOI: [10.1103/RevModPhys.93.015002](https://doi.org/10.1103/RevModPhys.93.015002).

DUAN, H.; FULLER, G. M.; QIAN, Y.-Z. Collective neutrino oscillations. **Annual Review of Nuclear and Particle Science**, v. 60, p. 569-594, 2010. DOI: [10.1146/annurev.nucl.012809.104524](https://doi.org/10.1146/annurev.nucl.012809.104524).

HALL, B.; ROGGERO, A.; BARONI, A.; CARLSON, J. Simulation of collective neutrino oscillations on a quantum computer. **Physical Review D**, v. 104, art. 063009, 2021. DOI: [10.1103/PhysRevD.104.063009](https://doi.org/10.1103/PhysRevD.104.063009).

ILLA, M.; SAVAGE, M. J. Multi-neutrino entanglement and correlations in dense neutrino systems. **Physical Review Letters**, v. 130, art. 221003, 2023. DOI: [10.1103/PhysRevLett.130.221003](https://doi.org/10.1103/PhysRevLett.130.221003).

JANKA, H.-T. Explosion mechanisms of core-collapse supernovae. **Annual Review of Nuclear and Particle Science**, v. 62, p. 407-451, 2012. DOI: [10.1146/annurev-nucl-102711-094901](https://doi.org/10.1146/annurev-nucl-102711-094901).

KISS, O.; TAVERNELLI, I.; TACCHINO, F.; LACROIX, D.; ROGGERO, A. Neutrino thermalization via randomization on a quantum processor. **Communications Physics**, v. 9, art. 282, 2026. DOI: [10.1038/s42005-026-02697-2](https://doi.org/10.1038/s42005-026-02697-2).

LACROIX, D.; BALANTEKIN, A. B.; CERVIA, M. J.; PATWARDHAN, A. V.; SIWACH, P. Role of non-gaussian quantum fluctuations in neutrino entanglement. **Physical Review D**, v. 106, art. 123006, 2022. DOI: [10.1103/PhysRevD.106.123006](https://doi.org/10.1103/PhysRevD.106.123006).

LACROIX, D.; BAUGE, A.; YILMAZ, B.; MANGIN-BRINET, M.; ROGGERO, A.; BALANTEKIN, A. B. Phase-space methods for neutrino oscillations: extension to multibeams. **Physical Review D**, v. 110, art. 103027, 2024. DOI: [10.1103/PhysRevD.110.103027](https://doi.org/10.1103/PhysRevD.110.103027).

MANGIN-BRINET, M.; BAUGE, A.; LACROIX, D. Three-flavor neutrino oscillations using the phase space approach. **Physical Review D**, v. 113, art. 036026, 2026. DOI: [10.1103/yr2g-1g2g](https://doi.org/10.1103/yr2g-1g2g).

NAGAKURA, H. Roles of fast neutrino-flavor conversion on the neutrino-heating mechanism of core-collapse supernova. **Physical Review Letters**, v. 130, art. 211401, 2023. DOI: [10.1103/PhysRevLett.130.211401](https://doi.org/10.1103/PhysRevLett.130.211401).

NOBEL PRIZE. **The Nobel Prize in Physics 2015: press release**. 6 Oct. 2015. Available at: https://www.nobelprize.org/prizes/physics/2015/press-release/. Accessed: 23 Oct. 2026.

RICCIO, M.; BALANTEKIN, A. B. Improved approximations for collective neutrino oscillations. **arXiv**, 2026. Preprint, arXiv:2607.28619, version 2. DOI: [10.48550/arXiv.2607.28619](https://doi.org/10.48550/arXiv.2607.28619). Available at: [arXiv](https://arxiv.org/abs/2607.28619). Accessed: 23 Oct. 2026.

SARMAH, P. et al. **Neutrino mass ordering from the next Galactic supernova at DUNE, HK, and JUNO**. Preprint, 2026. arXiv:2606.06580. Available at: https://arxiv.org/abs/2606.06580. Accessed: 23 Oct. 2026.

VISSANI, F.; COSTANTINI, M. L.; FULGIONE, W.; IANNI, A.; PAGLIAROLI, G. **What is the issue with SN1987A neutrinos?** Preprint, 2010. arXiv:1008.4726. Available at: https://arxiv.org/abs/1008.4726. Accessed: 23 Oct. 2026.
