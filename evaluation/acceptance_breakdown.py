"""Accept / amend / deny breakdown for the ISCDT 2026 campaign.

Run from the iscdt-2026 folder:

    python3 evaluation/acceptance_breakdown.py

It imports the campaign in evaluation/statistical_analysis.py and uses the same seeds
(run_id * 1000 + 42) as main(), so the numbers match statistical_report.txt.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import statistical_analysis as sa  # noqa: E402


def main() -> None:
    accepted = amended = denied = zeno = 0
    total = 0
    for run_id in range(sa.N_RUNS):
        r = sa.run_single_experiment(run_id, run_id * 1000 + 42, enable_dsf=True)
        accepted += r.accepted_count
        amended += r.amended_count
        denied += r.denied_count
        zeno += r.zeno_denied_count
        total += sa.N_INTENTS
    assert accepted + amended + denied == total
    print(f"Total intents      : {total}")
    print(f"Accepted           : {accepted} ({accepted / total:.2%})")
    print(f"Amended            : {amended} ({amended / total:.2%})")
    print(f"Denied             : {denied} ({denied / total:.2%})")
    print(f"  of which Zeno    : {zeno}")
    print(f"Accepted only      : {accepted / total:.2%}  <- the figure stored as 'acceptance_rate'")
    print(f"Accepted + amended : {(accepted + amended) / total:.2%}  <- the paper's 'including amendment'")


if __name__ == "__main__":
    main()
