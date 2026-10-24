"""Per-run results and per-gate denial breakdown for the ISCDT 2026 campaign.

Run from the repository root:

    python3 evaluation/campaign_details.py

It replays the campaign in evaluation/statistical_analysis.py with the same seeds
(run_id * 1000 + 42) and the same intent generator and gate functions, and records why
each intent was accepted, amended or denied. The replay is checked against
run_single_experiment() for every run, so the counts match statistical_report.txt.

Outputs (deterministic, no timing data):
    evaluation/results/per_run.csv
    evaluation/results/campaign_breakdown.md
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import statistical_analysis as sa  # noqa: E402

OUT_DIR = os.path.join(HERE, "results")

FIELDS = [
    "run_id", "seed", "intents",
    "accepted", "amended", "denied",
    "denied_gate1_schema", "denied_gate2_lyapunov", "denied_gate2_unamendable",
    "denied_gate3_zeno",
    "nominal", "nominal_accepted", "nominal_amended", "nominal_denied",
    "adversarial", "adversarial_accepted", "adversarial_amended", "adversarial_denied",
    "malformed",
    "safety_violations",
    "acceptance_rate_accepted_only", "acceptance_rate_with_amended",
]


def classify_gate2_denial(intent: sa.Intent) -> str:
    """Repeat gate2_cbf's decision logic to tell the two denial causes apart."""
    margins, all_passed = sa.compute_cbf_barriers(intent.desired_state.copy())
    if all_passed:
        return "lyapunov"  # barriers hold but V >= 5000 in gate2_cbf
    return "unamendable"   # barriers violated and the amended state is still unsafe


def replay_run(run_id: int) -> dict:
    seed = run_id * 1000 + 42
    rng = np.random.default_rng(seed)
    row = {k: 0 for k in FIELDS}
    row["run_id"], row["seed"], row["intents"] = run_id, seed, sa.N_INTENTS
    last_act_time = -1.0
    current_time = 0.0

    for _ in range(sa.N_INTENTS):
        current_time += rng.uniform(0.5, 3.0)
        intent = sa.generate_intent(rng, current_time)
        kind = "adversarial" if intent.is_adversarial else "nominal"
        row[kind] += 1
        if intent.is_malformed:
            row["malformed"] += 1

        decision, cause = sa.DECISION_ACCEPT, None
        g1_pass, _ = sa.gate1_cue(intent)
        if not g1_pass:
            decision, cause = sa.DECISION_DENY, "denied_gate1_schema"
        else:
            g2_decision, _, _ = sa.gate2_cbf(intent)
            if g2_decision == sa.DECISION_DENY:
                decision = sa.DECISION_DENY
                cause = ("denied_gate2_lyapunov"
                         if classify_gate2_denial(intent) == "lyapunov"
                         else "denied_gate2_unamendable")
            else:
                decision = g2_decision
                g3_pass, _ = sa.gate3_zeno(intent, last_act_time)
                if not g3_pass:
                    decision, cause = sa.DECISION_DENY, "denied_gate3_zeno"

        if decision == sa.DECISION_ACCEPT:
            row["accepted"] += 1
            row[f"{kind}_accepted"] += 1
            last_act_time = intent.timestamp
        elif decision == sa.DECISION_AMEND:
            row["amended"] += 1
            row[f"{kind}_amended"] += 1
            last_act_time = intent.timestamp
        else:
            row["denied"] += 1
            row[f"{kind}_denied"] += 1
            row[cause] += 1

        _, cbf_safe = sa.compute_cbf_barriers(intent.desired_state)
        if intent.is_adversarial and decision == sa.DECISION_ACCEPT and not cbf_safe:
            row["safety_violations"] += 1

    row["acceptance_rate_accepted_only"] = round(row["accepted"] / sa.N_INTENTS, 6)
    row["acceptance_rate_with_amended"] = round(
        (row["accepted"] + row["amended"]) / sa.N_INTENTS, 6)
    return row


def check_against_campaign(row: dict) -> None:
    ref = sa.run_single_experiment(row["run_id"], row["seed"], enable_dsf=True)
    got = (row["accepted"], row["amended"], row["denied"], row["denied_gate3_zeno"],
           row["safety_violations"])
    want = (ref.accepted_count, ref.amended_count, ref.denied_count,
            ref.zeno_denied_count, ref.safety_violations)
    if got != want:
        raise SystemExit(f"run {row['run_id']}: replay {got} != campaign {want}")


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:.2f} %" if d else "n/a"


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for run_id in range(sa.N_RUNS):
        row = replay_run(run_id)
        check_against_campaign(row)
        rows.append(row)

    with open(os.path.join(OUT_DIR, "per_run.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    t = {k: sum(r[k] for r in rows) for k in FIELDS if k not in (
        "run_id", "seed", "acceptance_rate_accepted_only", "acceptance_rate_with_amended")}
    N = t["intents"]

    lines = [
        "# ISCDT 2026 campaign: decision breakdown",
        "",
        "Generated by `evaluation/campaign_details.py` (seeds run_id * 1000 + 42, "
        f"{sa.N_RUNS} runs x {sa.N_INTENTS} intents). Every run was checked against "
        "`run_single_experiment()`; all counts match.",
        "",
        "## Decisions",
        "",
        "| Decision | Intents | Share |",
        "|---|---|---|",
        f"| Accepted | {t['accepted']} | {pct(t['accepted'], N)} |",
        f"| Amended | {t['amended']} | {pct(t['amended'], N)} |",
        f"| Denied | {t['denied']} | {pct(t['denied'], N)} |",
        f"| Accepted + amended | {t['accepted'] + t['amended']} | "
        f"{pct(t['accepted'] + t['amended'], N)} |",
        "",
        "## Why intents were denied",
        "",
        "| Cause | Intents | Share of all intents | Share of denials |",
        "|---|---|---|---|",
        f"| Gate 1, schema (malformed) | {t['denied_gate1_schema']} | "
        f"{pct(t['denied_gate1_schema'], N)} | {pct(t['denied_gate1_schema'], t['denied'])} |",
        f"| Gate 2, barriers hold but Lyapunov check fails | {t['denied_gate2_lyapunov']} | "
        f"{pct(t['denied_gate2_lyapunov'], N)} | {pct(t['denied_gate2_lyapunov'], t['denied'])} |",
        f"| Gate 2, barrier violated and not amendable | {t['denied_gate2_unamendable']} | "
        f"{pct(t['denied_gate2_unamendable'], N)} | "
        f"{pct(t['denied_gate2_unamendable'], t['denied'])} |",
        f"| Gate 3, Zeno guard | {t['denied_gate3_zeno']} | "
        f"{pct(t['denied_gate3_zeno'], N)} | {pct(t['denied_gate3_zeno'], t['denied'])} |",
        "",
        "## Nominal versus adversarial intents",
        "",
        "| Intent type | Intents | Accepted | Amended | Denied |",
        "|---|---|---|---|---|",
        f"| Nominal | {t['nominal']} | {pct(t['nominal_accepted'], t['nominal'])} | "
        f"{pct(t['nominal_amended'], t['nominal'])} | {pct(t['nominal_denied'], t['nominal'])} |",
        f"| Adversarial | {t['adversarial']} | {pct(t['adversarial_accepted'], t['adversarial'])} | "
        f"{pct(t['adversarial_amended'], t['adversarial'])} | "
        f"{pct(t['adversarial_denied'], t['adversarial'])} |",
        "",
        f"Malformed intents (any type): {t['malformed']}. "
        f"Safety violations with the filter: {t['safety_violations']}.",
        "",
        "Intents are drawn by the synthetic generator `generate_intent()`, not by a language "
        "model. These shares describe the filter's behaviour on that generator.",
        "",
    ]
    with open(os.path.join(OUT_DIR, "campaign_breakdown.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
