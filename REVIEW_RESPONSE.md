# Response to the ISCDT 2026 committee (MINOR REVISION)

Each item lists the reviewer's comment, the change made in this folder, and the work
still open for the author before the camera-ready deadline.

**Strengths.** No change required; the paper's novelty and evaluation claims are kept,
with the scope statements added below.

**1. Simulation versus reality.** Addressed in `LIMITATIONS.md`. Open: the paper must
add a short paragraph that refers to it and states the transfer limits.

**2. Scope of the guarantee.** Addressed in `ASSUMPTIONS.md` (section 5 now records the 200 ms versus 0.5 s conflict), which lists the system
model, barrier validity region, Lyapunov approximation, delay assumption and the
meaning of "Zeno-free". The phrase "100% Zeno-freeness" must be replaced in the paper
by "no violation of the minimum inter-actuation interval", using the wording in
section 6 of `ASSUMPTIONS.md`. The campaign used 200 ms, which matches the paper. The code default of 0.5 s must be changed or documented.

**3. Acceptance rate of 49.4 percent.** The figure is in `evaluation/statistical_report.txt`
as 49.36 percent, and a re-run reproduces it exactly (`RESULTS.md`). The stored rate counts accepted intents only; with amendments the figure is 68.9 percent (`RESULTS.md`), so the paper's phrase "including amendment" must be corrected. The rate comes from a
synthetic generator with 30 percent adversarial intents and 8 percent malformed intents
(`INTENT_MAPPING.md`, section 2). The paper must state this, and must add the split between
accepted, amended and denied, computed from the raw results. The split is now computed (`evaluation/acceptance_breakdown.py`). Open: the paper must report the split.

**4. Reproducibility.** Addressed in `INTENT_MAPPING.md`, `RESULTS.md` and `RELEASE.md`.
The campaign is seeded and re-runs exactly. Open: the author must confirm that the 50
intents-per-run campaign is the one described in the paper (the paper says 50,000 intents
in total, which matches 50 x 1000). The C++ core is not used by the campaign, and the
paper's "C++ DSF" statement must be corrected or the core must be wired in (`CPP_STATUS.md`).

**C++ question raised in the committee's strengths.** Addressed in `CPP_STATUS.md`. The C++ core exists but is not used by the evaluation, and it could not be compiled here.

**Summary.** The reviewers' main concern is scope. The folder now states that scope
explicitly. Items marked "Open" are data or statements that only the author can supply,
and none of them has been filled in here.
