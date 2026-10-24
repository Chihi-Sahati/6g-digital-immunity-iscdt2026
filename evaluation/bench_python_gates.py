"""Wall-clock latency of the campaign's Python gates, without the injected random term.

The campaign (evaluation/statistical_analysis.py) reports a per-intent "DSF latency" that
adds np.random.uniform terms to the measured time inside each gate. This script measures
the wall-clock time of the same gate calls (gate1_cue, gate2_cbf, gate3_zeno) for the same
50,000 intents and also records the latency value the campaign would report, so the two
can be compared.

Run from the repository root:

    python3 evaluation/bench_python_gates.py [out.csv]
"""
from __future__ import annotations

import csv
import os
import sys
import time
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:  # scipy is only needed by the campaign's statistics functions, not by the gates
    import scipy.stats  # noqa: F401
except ImportError:  # pragma: no cover
    scipy_stub = types.ModuleType("scipy")
    scipy_stub.stats = types.ModuleType("scipy.stats")
    sys.modules["scipy"] = scipy_stub
    sys.modules["scipy.stats"] = scipy_stub.stats

import statistical_analysis as sa  # noqa: E402


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results", "python_gate_latency.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows = []
    for run_id in range(sa.N_RUNS):
        rng = np.random.default_rng(run_id * 1000 + 42)
        last_act_time, current_time = -1.0, 0.0
        for _ in range(sa.N_INTENTS):
            current_time += rng.uniform(0.5, 3.0)
            intent = sa.generate_intent(rng, current_time)
            t0 = time.perf_counter()
            reported = 0.0
            ok1, l1 = sa.gate1_cue(intent)
            reported += l1
            decision = sa.DECISION_DENY
            if ok1:
                d2, l2, _ = sa.gate2_cbf(intent)
                reported += l2
                if d2 != sa.DECISION_DENY:
                    ok3, l3 = sa.gate3_zeno(intent, last_act_time)
                    reported += l3
                    if ok3:
                        decision = d2
                        last_act_time = intent.timestamp
            wall_ms = (time.perf_counter() - t0) * 1000.0
            rows.append((run_id, wall_ms, reported, decision))

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "wall_ms", "reported_ms", "decision"])
        w.writerows(rows)

    wall = np.array([r[1] for r in rows])
    rep = np.array([r[2] for r in rows])
    print(f"intents: {len(rows)}")
    print(f"wall-clock  mean {wall.mean()*1000:.1f} us, median {np.median(wall)*1000:.1f} us, "
          f"p99 {np.percentile(wall, 99)*1000:.1f} us")
    print(f"reported    mean {rep.mean():.3f} ms, median {np.median(rep):.3f} ms")


if __name__ == "__main__":
    main()
