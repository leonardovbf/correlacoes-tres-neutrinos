# Beyond mean field: does the phase-space approximation capture three-body neutrino correlations?

## Abstract

The phase-space approximation was evaluated for two- and three-body cumulants in a two-flavor neutrino model. Comparison with exact evolution indicated larger normalized triple errors in 14 of 15 main configurations, according to the recorded intervals. More measurements reduced ideal-circuit error; in the primary noisy case, readout mitigation did not recover the exact cumulant in simulation or on IBM hardware. Parameters, controls, and reproducibility materials are presented. Statistical review and noise-threshold evaluation remain necessary for confirmatory conclusions.

## Introduction

### Astrophysical context and motivation

Stars with initial masses above approximately eight solar masses can undergo gravitational core collapse. In a typical scenario, an iron-rich core loses support, contracts, and undergoes a bounce, generating a shock. This shock can stall through energy losses from nuclear dissociation and neutrino emission. Neutrino absorption and fluid motion can revive it during accretion, meaning matter falling onto the remnant (Figure 1) (JANKA, 2012; ABI et al., 2020).

![Three panels show a contracting stellar core, neutrino heating behind the shock, and the possible outcomes of explosion or black-hole formation.](figuras/en/figure-1-core-collapse.png)

*Figure 1 - Stellar core collapse, not to scale. (a) Core contraction and bounce. (b) Stalled shock and neutrino heating around the proto-neutron star (PNS). (c) Explosion or black-hole formation, including after an explosion. Source: original illustration based on Janka (2012).*

Neutrinos are electrically neutral elementary particles that interact weakly with matter. A typical supernova emits about $10^{58}$ neutrinos, with characteristic energies of $10\,\mathrm{MeV}$, over approximately ten seconds, carrying more than 99% of the gravitational energy released by the collapsed core (ABI et al., 2020). Their flavor states are superpositions of mass states, whose propagation phases change detection probabilities, producing oscillations (DUAN; FULLER; QIAN, 2010).

Flavor evolution can alter heating behind the shock and the neutron-to-proton composition relevant to nucleosynthesis. Its effects depend on stellar configuration, as shown by Nagakura (2023) and Akaho et al. (2026); the relationship between neutron-rich matter and heavy-element formation is discussed by Cowan et al. (2021). Events from SN 1987A and detection prospects at DUNE, Hyper-Kamiokande, and JUNO reinforce the importance of predicting emitted flavors (VISSANI et al., 2010; BAUM; CAPOZZI; HORIUCHI, 2022; SARMAH et al., 2026). Near the core, coherent interactions between neutrinos couple their evolution, generating collective oscillations and the many-body problem discussed next (DUAN; FULLER; QIAN, 2010).

### State of the art and research gap

The collective dynamics described above constitutes a quantum many-body problem in which correlations and entanglement can develop between neutrinos, with entanglement associated with the nonseparability of the joint quantum state. In the general two-flavor representation, a pure state of $N$ neutrinos has $2^N$ complex amplitudes. This growth limits exact evolution of large systems on classical computers when no specific symmetries or compression schemes are exploited (DUAN; FULLER; QIAN, 2010; CERVIA et al., 2019).

One strategy to reduce this cost is the mean-field approximation, which replaces the effects of other particles with an effective field determined by their averages. By factorizing expectation values of operators acting on distinct particles, this description neglects connected correlations and, for initially factorized states, does not track the generation of entanglement between neutrinos. [Cervia et al. (2019)](https://doi.org/10.1103/PhysRevD.100.083001) related differences between exact and mean-field evolution to the development of entanglement, with a dependence on initial conditions. In a three-flavor model, [Mangin-Brinet, Bauge, and Lacroix (2026)](https://doi.org/10.1103/yr2g-1g2g) also observed short-time deviations in the configurations examined. The validity of the approximation must therefore be assessed in terms of the model, initial conditions, and dynamical regime.

The phase-space approximation (PSA) seeks to incorporate effects beyond mean field through an ensemble of independent trajectories. Initial conditions are sampled to reproduce selected quantum moments, and each trajectory evolves according to mean-field equations; observables are estimated by statistical averages over the ensemble. [Lacroix et al. (2022)](https://doi.org/10.1103/PhysRevD.106.123006) obtained good agreement with mean values and entropies of one- and two-neutrino reduced states, calculated from their respective density matrices, in a two-beam model, although they did not reproduce long-time oscillations of fluctuations. The extension to multiple beams also compared collective two-body correlations through the covariance-based observable $C_{ZZ}$. This collective validation is not equivalent to assessing every pair individually and does not establish the accuracy of third-order cumulants ([LACROIX et al., 2024](https://doi.org/10.1103/PhysRevD.110.103027)). The extension to three flavors was subsequently compared with exact solutions for up to eight neutrinos ([MANGIN-BRINET; BAUGE; LACROIX, 2026](https://doi.org/10.1103/yr2g-1g2g)).

Another approach beyond mean field truncates the Bogoliubov–Born–Green–Kirkwood–Yvon (BBGKY) hierarchy, which relates the evolution of one-particle observables to higher-order correlations. In the preprint by [Riccio and Balantekin (2026)](https://arxiv.org/abs/2607.28619), the second-order closure retains pair contributions and sets connected three-body cumulants to zero to close the equations. This condition does not necessarily set the expectation value of a product of three operators to zero, because contributions constructed from individual means and pairs remain. PSA incorporates higher moments without imposing the same closure; its accuracy for third-order cumulants must be examined directly ([LACROIX et al., 2022](https://doi.org/10.1103/PhysRevD.106.123006)).

Quantum simulations offer a complementary route to investigate these correlations. [Hall et al. (2021)](https://doi.org/10.1103/PhysRevD.104.063009) demonstrated simulations of small neutrino systems on noisy devices, using error mitigation, namely techniques to reduce the effects of noise on observable estimates, to extract entanglement measures. [Illa and Savage (2023)](https://doi.org/10.1103/PhysRevLett.130.221003) investigated systems of up to twelve neutrinos on the Quantinuum H1-1 trapped-ion processor, including two- and three-body correlations and multipartite entanglement indicators. At a larger scale, [Kiss et al. (2026)](https://doi.org/10.1038/s42005-026-02697-2) studied thermalization with random circuits on IBM processors using more than one hundred qubits. Their performance was assessed through thermalization observables; the fidelity of specific cumulants during evolution requires separate validation.

Within the literature examined, no systematic comparison of PSA three-body cumulants with exact evolution was identified that controls system size, interaction strength, and computational and measurement uncertainties. Agreement in flavor averages, collective pair correlations, or reduced entropies does not guarantee accurate third-order cumulants. Addressing this gap requires consistent observables and a separation of approximation error, finite sampling, time discretization, and noise.

The accuracy of third-order cumulants matters because, for a Hamiltonian with pair interactions, the evolution hierarchy couples one-particle observables to two-body correlations, whose equations depend on third-order moments. Deviations in the description of triples may therefore affect lower-order observables during evolution ([LACROIX et al., 2024](https://doi.org/10.1103/PhysRevD.110.103027); [RICCIO; BALANTEKIN, 2026](https://arxiv.org/abs/2607.28619)). The reported long-time limitations of PSA motivate examining this relationship, without attributing all flavor deviations to a single cumulant component in advance ([LACROIX et al., 2022](https://doi.org/10.1103/PhysRevD.106.123006)).

For four to eight neutrinos, exact calculations are accessible on classical computers. The quantum stage seeks to determine how accurately circuits distinguish PSA deviations. In larger systems, without accessible exact solutions, these circuits could provide a reference for validating approximations. Small systems allow this possibility to be assessed by separating discretization, sampling, and noise errors, without presupposing a computational advantage or extrapolating the results to larger systems.

This work therefore asks in which regimes of interaction strength, system size, and evolution time PSA reproduces connected two- and three-body correlations and, when deviations occur, under which noise conditions and measurement counts quantum circuits can distinguish them from exact results.

To this end, the study proposes to assess connected two- and three-body cumulants from PSA against exact calculations, with mean field as an additional reference, establishing the approximation's validity regimes. Python will be used for systems of four to approximately sixteen neutrinos and Qiskit for circuits of four to eight, in a two-flavor model with factorized pure-flavor initial states. The ratio $\mu/\bar{\omega}$ will range from 0.1 to 10, where $\mu$ denotes the neutrino–neutrino interaction scale and $\bar{\omega}$ the mean vacuum oscillation frequency. The supernova context motivates the model; conclusions will remain restricted to the simplified configurations examined.

Increasing interaction strength increases the coefficients of the terms coupling the hierarchy's orders, motivating the expectation that triples are more sensitive to effects beyond mean-field trajectories. This is a conjecture dependent on the initial state and time window, not a consequence of PSA setting higher cumulants to zero. Hypothesis **H1** is that PSA reproduces individual flavor probabilities and two-body cumulants more accurately than three-body cumulants. When the reference permits normalization, the normalized error for triples tends to grow with interaction strength. Hypothesis **H2** predicts that mitigation increases the noise threshold at which PSA can be distinguished from exact evolution at the same total measurement budget. Their falsification criteria will be specified in the research design.

Section 2 presents the model, observables, comparison stages, and hypothesis assessment criteria. Section 3 describes the planned presentation of results. The present text sets out the research design; experimental results will be incorporated after the protocol has been executed and validated.

## Methodology

Mean field, PSA, and circuits are compared against exact evolution. The [protocol](PROTOCOLO_EXPERIMENTOS.md) records configurations, seeds, and checks.

Each neutrino corresponds to a qubit, with $|\nu_e\rangle=|0\rangle$ and $|\nu_x\rangle=|1\rangle$. With $\hbar=1$, $\tau=\bar{\omega}t$, $\lambda=\mu/\bar{\omega}$, and $\widetilde{\omega}_i=\omega_i/\bar{\omega}$,

$$
\frac{H}{\bar{\omega}}=\frac{1}{2}\sum_{i=0}^{N-1}\widetilde{\omega}_i\,\mathbf{B}\cdot\boldsymbol{\sigma}_i
+\frac{\lambda}{4N}\sum_{i<j}g_{ij}\,\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j.
$$

where $\mathbf{B}=(\sin2\theta,0,-\cos2\theta)$, $\boldsymbol{\sigma}_i$ denotes Pauli operators, and $g_{ij}$ defines coupling. Each pair appears once. The model excludes transport, collisions, and hydrodynamics; a fixed window in $\tau$ corresponds to $\mu t=\lambda\tau$.

The reference uses `expm_multiply` (SciPy), checked by dense exponentiation for a small system. Mean field and PSA use RK4. PSA samples independent transverse components as $\pm1$, with the longitudinal component fixed by flavor (LACROIX et al., 2024).

Circuits use symmetric second-order Trotter decomposition. Comparing Qiskit with the emulator checks implementation; comparison with exact evolution isolates discretization from sampling and noise.

For $m_i(t)=\langle Z_i\rangle_t$, the electron-flavor probability is $P_{e,i}(t)=[1+m_i(t)]/2$. Cumulants of distinct particles are

$$
\begin{aligned}
C^{(2)}_{ij}(t)&=\langle Z_i Z_j\rangle_t-m_i(t)m_j(t),\\
C^{(3)}_{ijk}(t)&=\langle Z_i Z_j Z_k\rangle_t-m_i(t)m_j(t)m_k(t)\\
&\quad-C^{(2)}_{ij}(t)m_k(t)-C^{(2)}_{ik}(t)m_j(t)-C^{(2)}_{jk}(t)m_i(t).
\end{aligned}
$$

Analysis is restricted to $Z$, $ZZ$, and $ZZZ$; nonzero cumulants alone do not certify entanglement.

Checks cover published reproduction, zero interaction, integration, sampling, and Trotter error. Failures require documented amendments, without excluding unfavorable results.

## Experiments and parameters

The grid contains fifteen main configurations and ten extension configurations (Table 1), with a fixed association between frequency and initial flavor.

*Table 1 - Parameters of the original classical grid.*

| Parameter | Definition |
| --- | --- |
| Sizes and interaction | $N=4,6,8$; extension: $12,16$. $\lambda=0.1,0.3,1,3,10$. |
| Frequencies and mixing | $\widetilde{\omega}_i=0.7+0.6i/(N-1)$, $i=0,\ldots,N-1$; $\theta=0.2$ rad. |
| Couplings | $g_{ij}=1$ for $i\ne j$; $g_{ii}=0$. |
| Initial state | First half of indices in $\nu_e$; second half in $\nu_x$. |
| Time and integration | $0\leq\tau\leq10$, 201 times; 12 RK4 substeps per interval. |
| Observables | All distinct individuals, pairs, and triples. |
| PSA and seeds | 20 independent blocks of 4,096 trajectories (81,920 total); seeds 10,001–10,020. |

Reproduction of Lacroix et al. (2024) uses Figure 2(c) of that study, in a configuration distinct from Table 1, with eight neutrinos and 10,000 trajectories. Coordinates were extracted from the figure; parameters and conversions appear in the [reference documentation](data/benchmarks/lacroix2024/README.md).

Convergence at $N=4,8$ and $\lambda=0.1,1,10$ varies trajectories, RK4 substeps, and Trotter steps. Table 3 bounds maximum absolute deviations, refinement from 8 to 12 substeps, and the largest standard error across seeds, over times and triples.

Ideal circuits use $N=4,6,8$ and twenty blocks of 1,024, 4,096, or 16,384 shots per time. The noisy stage is restricted to $N=4$, triple $(0,1,2)$, and $\tau=1,2,4$, retaining the five interactions and three budgets. The original discretization totals 112 Trotter steps.

*Table 2 - Noise profiles defined for the Aer simulator.*

| Profile | Depolarization: one qubit | Depolarization: two qubits | Readout error |
| --- | ---: | ---: | ---: |
| Ideal | 0 | 0 | 0 |
| Mild | 0.0001 | 0.001 | 0.01 |
| Moderate | 0.001 | 0.01 | 0.03 |

Aer uses density-matrix simulation, the `rz`, `sx`, `x`, `cx` basis, and optimization level 1. The synthetic profiles in Table 2 apply depolarization to `sx`, `x`, `cx` and independent symmetric readout flips.

Mitigation inverts the tensor product of response matrices calibrated with $|0000\rangle$ and $|1111\rangle$, retaining negative quasiprobabilities. Per block, it assigns $3m/4$ shots to signal and $m/8$ to each calibration; the raw method uses $m$ for signal. Both receive $M=20m$. This correction does not remove gate errors.

The primary case uses $N=4$, $\lambda=3$, $\tau=2$, moderate noise, and $m=16,384$, with an additional execution on `ibm_kingston`.

Amendment v3 followed detection of an omitted sampling check and its failure in three of six configurations. It added twenty blocks of 4,096 trajectories per configuration, passing under the same limit. Reanalysis preserved the original failure.

After the Trotter check failed, v4 used 29 points and 448 steps at $N=4$, $\lambda=10$, $\tau=4$; at $\lambda=10$, $\tau=2$, PSA increased from 12 to 24 RK4 substeps. The primary case was unchanged. Different depths limit comparisons across interaction strengths.

## Evaluation metrics

For $T$ times and $n_q$ particle sets, let $O^{\mathrm{ex}}_{q,\alpha}$ be the reference and $\widehat O_{q,\alpha}$ the estimate of $P_e$, $C^{(2)}$, or $C^{(3)}$. Define

$$
\begin{aligned}
E_q&=\sqrt{\frac{1}{Tn_q}\sum_{\ell=1}^{T}\sum_{\alpha=1}^{n_q}
\left[\widehat{O}_{q,\alpha}(\tau_\ell)-O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)\right]^2},\\
S_q&=\sqrt{\frac{1}{Tn_q}\sum_{\ell=1}^{T}\sum_{\alpha=1}^{n_q}
\left[O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)\right]^2}.
\end{aligned}
$$

Use $R_q=E_q/S_q$ for $S_q\geq10^{-4}$ and only absolute error below this floor. For H1, $D=R_3-R_2$ receives 2,000 bootstrap replicates of independent blocks. Moments are pooled before cumulants, preserving temporal dependence; the 2.5th and 97.5th percentiles define the 95% interval.

Circuits use 2,000 multinomial replicates of aggregated counts, reestimating calibration and independently resampling PSA blocks, without bias correction. For $C^{(3)}$, let $I_{\mathrm{PSA}}$ denote the circuit-minus-PSA interval and $[L,U]$ the circuit-minus-exact interval. Resolution requires

$$
0\notin I_{\mathrm{PSA}}
\quad\text{and}\quad
[L-r,U+r]\subseteq[-\delta,\delta],
\qquad \delta=0.01,
$$

where $r$ adds the ideal-minus-exact deviation to $10^{-5}$. A nonfinite calibration condition number or one above 10 makes the case unresolved.

For H2, $p_{\max}(M)$ is the largest evaluated noise level satisfying the criterion at budget $M$. Comparing thresholds with and without mitigation requires a fixed noise family, sweep, and relevance margin; the current grid does not estimate this difference.

*Table 3 - Tolerances and selected checks. Maxima over each control's configurations; dashes indicate values not reproduced in this summary.*

| Control | Limit | Observed |
| --- | ---: | ---: |
| Published reproduction: exact | $2\times10^{-2}$ | $1.41\times10^{-3}$ |
| Published reproduction: PSA | $6\times10^{-2}$ | $2.99\times10^{-2}$ |
| Independent exact reference | $10^{-10}$ | — |
| Qiskit versus emulator | $10^{-10}$ | $2.80\times10^{-12}$ |
| RK4 refinement: $P_e$ | $10^{-6}$ | — |
| RK4 refinement: cumulants | $10^{-5}$ | — |
| Supplementary PSA standard error: $C^{(3)}$ | $10^{-2}$ | $5.11\times10^{-3}$ |
| Ideal Trotter: $C^{(3)}$ | $10^{-3}$ | — |

## Experimental results

### Validation and PSA accuracy

The eleven local phases, including $N=12,16$, passed the checks after amendments (Table 3). Published-reproduction deviations include figure-extraction uncertainty.

The 95% interval for $D$ was positive in 14 of 15 main configurations (Figure 2). At $N=4$, $\lambda=0.1$, its sign remained unresolved: $D=-0.132$, interval $[-0.209,0.048]$. At $N=4$, $\lambda=3$, estimates were $R_2=0.419$, $R_3=0.948$, and $D=0.529$, interval $[0.524,0.535]$.

![Three panels show the difference between normalized triple and pair errors, with point estimates and percentile intervals for the main grid.](figuras/en/figure-5-psa-results.png)

*Figure 2 - $D=R_3-R_2$ for $0\leq\tau\leq10$: estimates from twenty PSA blocks and 95% percentile intervals from 2,000 replicates. The open circle marks the estimate outside its own interval. Source: original plot from the results package.*

All ten extension intervals were positive. However, five estimates fell outside their own intervals: $N=8$, $\lambda=0.1$, and $N=12,16$, $\lambda=0.1$ and $0.3$. These and the aggregated slopes for $N=8,12,16$ require review of bootstrap bias. A global conclusion about H1 requires criteria for aggregation, relevance, and multiplicity.

Larger triple errors do not grow monotonically with interaction strength: at $N=8$, $D$ falls from $0.485$ to $0.363$ between $\lambda=0.1$ and $1$, before increasing.

### Measurement budget

In ideal circuits, $C^{(3)}$ RMSE decreased with each budget increase in all fifteen configurations. From 1,024 to 16,384 shots per block, reduction factors of 3.75–4.19 (Figure 3) approach the factor of four expected from $1/\sqrt{m}$ dependence. Three budgets do not establish a scaling law or assess gate errors.

![Three panels show triple-cumulant RMSE versus shots per block for the three main system sizes and five interaction strengths.](figuras/en/figure-6-measurement-budget.png)

*Figure 3 - Triple RMSE relative to exact evolution, aggregated over times and triples. Each point uses twenty blocks of $m$ shots per time; lines connect budgets, without confidence intervals. Source: original plot from the results package.*

### Noise, mitigation, and hardware

In the primary case, the exact cumulant was $-0.315784$; PSA estimated $-0.155768$ from local blocks and $-0.151947$ from IBM-associated blocks, distinct samples. Noisy circuits remained close to zero with and without mitigation (Table 4 and Figure 4).

*Table 4 - Primary case: estimates of $C^{(3)}$ and 95% intervals for circuit minus exact, widened by the numerical residual. Each method receives $M=327,680$ shots; calibration is included in the mitigated budget.*

| Environment | Method | Estimate | 95% CI of difference |
| --- | --- | ---: | --- |
| Aer | Raw | $-0.000305$ | $[0.312040,0.318866]$ |
| Aer | Mitigated | $0.001301$ | $[0.312190,0.322029]$ |
| IBM | Raw | $0.005847$ | $[0.317702,0.325733]$ |
| IBM | Mitigated | $0.006376$ | $[0.317486,0.327007]$ |

![Comparison of the exact cumulant, the two PSA estimates, and Aer and IBM circuits without and with mitigation in the primary case.](figuras/en/figure-7-quantum-comparison.png)

*Figure 4 - Primary case: band of $\pm0.01$ around the exact value; circuit intervals widened by the residual and translated to $C^{(3)}$. PSA has no individual interval; circles and squares represent raw and mitigated methods. Source: original plot from the results package.*

All four circuit-minus-PSA intervals exclude zero, but no circuit-minus-exact interval fits within $[-0.01,0.01]$. Mitigation did not recover the cumulant within this margin. The pointwise decision is inconclusive and does not test the H2 noise threshold.

IBM completed twenty blocks, four qubits, eighty jobs, and 655,360 shots including calibrations in 72.87 minutes. The report retains provisional scientific status despite completion of all jobs; detailed timings are in the results package.

Conclusions are restricted to the model, initial state, and components studied. The [repository](https://github.com/leonardovbf/correlacoes-tres-neutrinos) provides code, protocols, workloads, the reference dataset, and auditable results. The complete trajectory and count archive in `results/`, required for full reanalysis, is not included in the package.

## Use of generative artificial intelligence

Generative artificial intelligence assistance was used to support writing and text revision, translation, organization of the methodological description from code and protocols, and production of code for the conceptual diagrams.

## References

Abi, B. et al. (2020). Deep Underground Neutrino Experiment (DUNE), Far Detector Technical Design Report, Volume II: DUNE Physics. Technical Report FERMILAB-PUB-20-025-ND, DUNE Collaboration. <https://arxiv.org/abs/2002.03005>.

Akaho, R., Nagakura, H., Iwakami, W., Furusawa, S., Harada, A., Okawa, H., Matsufuru, H., Sumiyoshi, K., and Yamada, S. (2026). Bifurcated Impact of Neutrino Fast Flavor Conversion on Core-Collapse Supernovae Informed by Multiangle Neutrino Radiation Hydrodynamics. *Physical Review Letters*, 136(19):191002. <https://doi.org/10.1103/fksy-1jtw>.

Baum, S., Capozzi, F., and Horiuchi, S. (2022). Rocks, water, and noble liquids: Unfolding the flavor contents of supernova neutrinos. *Physical Review D*, 106(12):123008. <https://doi.org/10.1103/PhysRevD.106.123008>.

Cervia, M. J., Patwardhan, A. V., Balantekin, A. B., Coppersmith, S. N., and Johnson, C. W. (2019). Entanglement and collective flavor oscillations in a dense neutrino gas. *Physical Review D*, 100(8):083001. <https://doi.org/10.1103/PhysRevD.100.083001>.

Cowan, J. J., Sneden, C., Lawler, J. E., Aprahamian, A., Wiescher, M., Langanke, K., Martínez-Pinedo, G., and Thielemann, F.-K. (2021). Origin of the heaviest elements: The rapid neutron-capture process. *Reviews of Modern Physics*, 93(1):015002. <https://doi.org/10.1103/RevModPhys.93.015002>.

Duan, H., Fuller, G. M., and Qian, Y.-Z. (2010). Collective Neutrino Oscillations. *Annual Review of Nuclear and Particle Science*, 60(1):569--594. <https://doi.org/10.1146/annurev.nucl.012809.104524>.

Hall, B., Roggero, A., Baroni, A., and Carlson, J. (2021). Simulation of collective neutrino oscillations on a quantum computer. *Physical Review D*, 104(6):063009. <https://doi.org/10.1103/PhysRevD.104.063009>.

Illa, M. and Savage, M. J. (2023). Multi-Neutrino Entanglement and Correlations in Dense Neutrino Systems. *Physical Review Letters*, 130:221003. <https://doi.org/10.1103/PhysRevLett.130.221003>.

Janka, H.-T. (2012). Explosion Mechanisms of Core-Collapse Supernovae. *Annual Review of Nuclear and Particle Science*, 62:407--451. <https://doi.org/10.1146/annurev-nucl-102711-094901>.

Kiss, O., Tavernelli, I., Tacchino, F., Lacroix, D., and Roggero, A. (2026). Neutrino thermalization via randomization on a quantum processor. *Communications Physics*, 9(1):282. <https://doi.org/10.1038/s42005-026-02697-2>.

Lacroix, D., Balantekin, A. B., Cervia, M. J., Patwardhan, A. V., and Siwach, P. (2022). Role of non-Gaussian quantum fluctuations in neutrino entanglement. *Physical Review D*, 106(12):123006. <https://doi.org/10.1103/PhysRevD.106.123006>.

Lacroix, D., Bauge, A., Yilmaz, B., Mangin-Brinet, M., Roggero, A., and Balantekin, A. B. (2024). Phase-space methods for neutrino oscillations: Extension to multibeams. *Physical Review D*, 110:103027. <https://doi.org/10.1103/PhysRevD.110.103027>.

Mangin-Brinet, M., Bauge, A., and Lacroix, D. (2026). Three-flavor neutrino oscillations using the phase space approach. *Physical Review D*, 113:036026. <https://doi.org/10.1103/yr2g-1g2g>.

Nagakura, H. (2023). Roles of Fast Neutrino-Flavor Conversion on the Neutrino-Heating Mechanism of Core-Collapse Supernova. *Physical Review Letters*, 130(21):211401. <https://doi.org/10.1103/PhysRevLett.130.211401>.

Riccio, M. and Balantekin, A. B. (2026). Improved Approximations for Collective Neutrino Oscillations. Preprint, version 2. <https://doi.org/10.48550/arXiv.2607.28619>.

Sarmah, P., Chakraborty, S., Medhi, A., Bose, D., and Devi, M. M. (2026). Neutrino mass ordering from the next Galactic supernova at DUNE, HK, and JUNO. Preprint. <https://arxiv.org/abs/2606.06580>.

Vissani, F., Costantini, M. L., Fulgione, W., Ianni, A., and Pagliaroli, G. (2010). What is the issue with SN1987A neutrinos? Preprint. <https://arxiv.org/abs/1008.4726>.
