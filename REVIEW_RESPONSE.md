# Response to the ISCDT 2026 committee (MINOR REVISION): repository side

Each item lists what the repository now provides. Items marked "Paper" must be carried
into the manuscript.

**1. Simulation versus reality.** `LIMITATIONS.md` describes the OU-process model, the
missing testbed, the latency caveats and the synthetic intent generator.
Paper: add a limitations paragraph based on it.

**2. Scope of the guarantee.** `ASSUMPTIONS.md` lists the system model, barrier validity
region, the Lyapunov check actually used (a static threshold), the delay assumption and
the meaning of "Zeno-free". Code, campaign and paper now share tau_min = 200 ms.
Zero safety violations and zero Zeno violations follow from the construction of the
campaign and are documented as such.
Paper: replace "mathematically guaranteed safety" and "100% Zeno-freeness" with scoped
statements (section 6 of `ASSUMPTIONS.md`).

**3. Acceptance rate.** `evaluation/results/campaign_breakdown.md`: 49.36 percent accepted,
19.51 percent amended, 31.12 percent denied. 74.4 percent of denials come from the static
Lyapunov threshold applied to intents that satisfy all barriers; 41 percent of nominal
intents are denied. The rate reflects conservative filtering, not intent quality.
Paper: correct "49.4% including amendment" (the figure excludes amendments; with them it
is 68.9 percent) and discuss the threshold as the safety/throughput trade-off.

**4. Reproducibility.** The code is public; the campaign is seeded and deterministic;
per-run results are committed (`RELEASE.md`). The campaign uses a synthetic intent
generator and no language model (`INTENT_MAPPING.md`). The gate logic and the amendment
rule are written out in `INTENT_MAPPING.md`.
Paper: state that the intents are synthetic, describe the mapping, and cite tag
`iscdt-2026-v1.1`.

**C++ implementation (raised in the strengths).** `CPP_STATUS.md`: the core builds and
passes its tests in CI, one defect was fixed, but the campaign does not call it and its
latency is not measured.
Paper: do not present the 1.56 ms figure as C++ latency.
