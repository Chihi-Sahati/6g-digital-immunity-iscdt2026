# Erratum: nominal-intent generator (fixed in iscdt-2026-v1.2)

## The error

In `evaluation/statistical_analysis.py`, `generate_intent()` unpacked the three values
of a nominal (non-adversarial) intent in the wrong order:

    desired_tx, desired_prb, desired_hyst = (U(15, 38), U(1, 5), U(20, 75))

so every nominal intent requested a handover hysteresis of 20-75 dB and a PRB
utilisation of 1-5 %, instead of 1-5 dB and 20-75 %. The adversarial branches used the
correct order. The error is present in the snapshot (`snapshot-996c6c0`) and in tags
`iscdt-2026-v1` and `iscdt-2026-v1.1`, and therefore in the results of the ISCDT 2026
submission.

## Why it mattered

The barrier set has no upper bound on hysteresis, so these intents passed Gate 2's
barriers, but their distance to the reference point x_ref = (30 dBm, 3 dB, 50 %) put
V = ||x_d - x_ref||^2 above the admission threshold of 5000. The Lyapunov check then
denied 11,573 nominal intents. This, not a property of the filter, produced the low
acceptance rate.

## Effect of the fix (same seeds, same filter, 50 runs x 1000 intents)

| Quantity | Before (v1, v1.1) | After (v1.2) |
|---|---|---|
| Accepted without amendment | 49.36 % | 72.51 % |
| Amended | 19.51 % | 19.51 % |
| Denied | 31.12 % | 7.98 % (all malformed, Gate 1) |
| Denied by the Lyapunov threshold | 11,573 | 0 |
| Safety violations with the filter | 0 | 0 |
| Safety violations without the filter (per run) | 212.1 | 212.1 |

Adversarial intents, amendments and the safety result are unchanged, because the
adversarial branches were correct. The Lyapunov threshold is not binding at V_max = 5000
after the fix; `evaluation/results/vmax_sweep.csv` shows where it becomes binding.

## What was regenerated

`evaluation/statistical_report.txt`, `evaluation/statistical_plots/`,
`evaluation/results/` and `evaluation/figures/`, and every number in the documentation.
