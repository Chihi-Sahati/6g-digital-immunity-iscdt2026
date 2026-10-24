# Results, and how to regenerate them (v1.2)

All numbers below come from the corrected campaign (see `ERRATUM.md`).

    python3 evaluation/statistical_analysis.py   # statistical_report.txt and plots
    python3 evaluation/campaign_details.py       # per-run results and denial causes
    python3 evaluation/paper_figures.py          # figures, ablation, V_max sweep, numbers
    python3 evaluation/bench_python_gates.py     # measured Python gate latency
    # C++ latency: see the header of tests/bench_cbf_core.cpp

## Decisions (50 runs x 1000 intents)

| Decision | Intents | Share |
|---|---|---|
| Accepted | 36,255 | 72.51 % |
| Amended | 9,757 | 19.51 % |
| Denied (all by the schema gate) | 3,988 | 7.98 % |
| Accepted + amended | 46,012 | 92.02 % |

Per run, accepted without amendment: mean 0.7251, std 0.0139, 95 % CI [0.7211, 0.7291].
Nominal intents: 92.0 % accepted, 8.0 % denied (malformed). Adversarial intents: 26.8 %
accepted (they satisfy the barriers), 65.3 % amended, 8.0 % denied (malformed).
Safety violations: 0 with the filter, 212.1 per run without it.

## Ablation (`evaluation/results/ablation.csv`)

Removing Gate 2 gives 195.1 violations per run; removing Gate 1 or Gate 3 gives none.

## Lyapunov threshold (`evaluation/results/vmax_sweep.csv`)

At V_max = 5000 the threshold denies nothing. Lowering it trades throughput for a tighter
operating region: at V_max = 500, 69.3 % of intents are admitted; at V_max = 100, 34.9 %.
There are no safety violations at any threshold, because safety is enforced by the
barriers, not by the threshold.

## Latency (`evaluation/results/cpp_eval_us.csv`, `python_gate_latency.csv`)

- C++ core, four barriers + Lyapunov: 0.30 us mean, 0.37 us p99.
- Python gate pipeline, wall clock: 17 us mean, 77 us p99.
- The campaign's reported "DSF latency" (1.58 ms mean) adds random terms and is not a
  measurement.

Machine: Intel Core Ultra 7 255H, Linux VM with 2 vCPUs.
