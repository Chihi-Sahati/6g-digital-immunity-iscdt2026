# Results, and how to regenerate them

Command, from this folder:

    python3 evaluation/statistical_analysis.py

Output: `evaluation/statistical_report.txt` and `evaluation/statistical_plots/`.

Verified on 24 October 2026 (Python 3, numpy, scipy, matplotlib):

| Quantity | Paper | Repository report (commit 996c6c0) | Re-run |
|---|---|---|---|
| Runs x intents | 50 x 50,000 | 50 x 1000 | 50 x 1000 |
| Acceptance (accepted and amended) | 49.4 percent | 49.36 percent | 49.36 percent |
| Mean DSF latency | sub-1.6 ms | 1.56 ms | 1.57 ms |
| Zeno violations | 0 | 0.0 | 0.0 |
| Baseline violations per run | not stated | 212.1 | 212.1 |

The acceptance rate and the violation counts are reproducible because they use seeded
random generators. The latency varies with machine load and is not reproducible in the
strict sense.

## Acceptance breakdown (added 24 October 2026)

Command: `python3 evaluation/acceptance_breakdown.py`

| Decision | Intents | Share |
|---|---|---|
| Accepted | 24,682 | 49.36 percent |
| Amended | 9,757 | 19.51 percent |
| Denied | 15,561 | 31.12 percent |
| Accepted + amended | 34,439 | 68.88 percent |

The stored `acceptance_rate` counts accepted intents only. The paper's claim of 49.4 percent
"including amendment" is therefore incorrect. The correct statement is 68.9 percent accepted
or amended, 49.4 percent accepted without amendment.
