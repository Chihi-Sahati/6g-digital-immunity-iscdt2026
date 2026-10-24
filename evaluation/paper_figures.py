"""Figures and tables of the revised ISCDT 2026 paper, generated from the simulation code.

Every number and figure comes from code in this repository:

- RAN telemetry: simulation/ran_simulator.py (RANSimulator.generate_telemetry), run
  without Kafka through a stub producer, at 3.5 GHz and 140 GHz.
- Decisions, ablation and the Lyapunov-threshold sweep: the campaign in
  evaluation/statistical_analysis.py (same intent generator, gates and seeds).
- Latency: evaluation/results/cpp_eval_us.csv (tests/bench_cbf_core.cpp) and
  evaluation/results/python_gate_latency.csv (evaluation/bench_python_gates.py).

Run from the repository root:

    python3 evaluation/paper_figures.py

Outputs: evaluation/figures/*.pdf, evaluation/results/{ablation,vmax_sweep}.csv,
evaluation/results/paper_numbers.json.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "simulation"))

import statistical_analysis as sa  # noqa: E402  (also sets matplotlib to Agg)
import matplotlib.pyplot as plt  # noqa: E402

RES = os.path.join(HERE, "results")
FIG = os.path.join(HERE, "figures")
os.makedirs(RES, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

# Validated categorical slots (light surface), in fixed order.
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED = "#222222", "#6b6b6b"

plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6, "axes.grid": True,
    "grid.color": "#dddddd", "grid.linewidth": 0.5, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 1.2, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
})
W1 = 3.45  # IEEE single-column width in inches

X_REF = np.array([30.0, 3.0, 50.0])


# ---------------------------------------------------------------------------
# 1. RAN telemetry from the simulator itself
# ---------------------------------------------------------------------------
def run_ran(freq_ghz: float, steps: int, seed: int) -> dict:
    stub = types.ModuleType("confluent_kafka")

    class _Producer:  # the simulator only needs a constructor here
        def __init__(self, *_a, **_k):
            pass

    stub.Producer = _Producer
    sys.modules["confluent_kafka"] = stub
    os.environ["CARRIER_FREQ_GHZ"] = str(freq_ghz)
    os.environ["SIMULATION_INTERVAL_SEC"] = "1.0"
    import importlib
    import ran_simulator
    importlib.reload(ran_simulator)
    ran_simulator.logger.disabled = True
    np.random.seed(seed)
    sim = ran_simulator.RANSimulator()
    out = {"prb": [], "rsrp": [], "sinr": [], "fspl_penalty": sim.fspl_penalty}
    for _ in range(steps):
        sim.generate_telemetry()
        out["prb"].append(sim.prb_utilization)
        out["rsrp"].append(sim.rsrp)
        out["sinr"].append(sim.sinr)
    return out


def fig_telemetry(numbers: dict) -> None:
    steps, seed = 600, 2026
    lo, hi = run_ran(3.5, steps, seed), run_ran(140.0, steps, seed)
    t = np.arange(1, steps + 1)
    fig, ax = plt.subplots(3, 1, figsize=(W1, 3.3), sharex=True)
    ax[0].plot(t, hi["prb"], color=C1, label="PRB utilisation")
    ax[0].set_ylabel("PRB (%)")
    ax[0].set_ylim(0, 100)
    for a, key, unit in ((ax[1], "rsrp", "RSRP (dBm)"), (ax[2], "sinr", "SINR (dB)")):
        a.plot(t, lo[key], color=C1, label="3.5 GHz")
        a.plot(t, hi[key], color=C2, label="140 GHz")
        a.set_ylabel(unit)
    ax[1].legend(loc="center right", frameon=False, ncol=2)
    ax[2].set_xlabel("Time (s), 1 s sampling interval")
    fig.align_ylabels(ax)
    fig.savefig(os.path.join(FIG, "fig_telemetry.pdf"))
    plt.close(fig)
    burn = 100  # discard the transient from the initial state
    numbers["telemetry"] = {
        "steps": steps, "seed": seed, "burn_in": burn,
        "fspl_penalty_140_db": round(hi["fspl_penalty"], 2),
        "prb_mean": round(float(np.mean(hi["prb"][burn:])), 1),
        "prb_std": round(float(np.std(hi["prb"][burn:])), 1),
        "rsrp_mean_3p5": round(float(np.mean(lo["rsrp"][burn:])), 1),
        "rsrp_mean_140": round(float(np.mean(hi["rsrp"][burn:])), 1),
        "sinr_mean_3p5": round(float(np.mean(lo["sinr"][burn:])), 1),
        "sinr_mean_140": round(float(np.mean(hi["sinr"][burn:])), 1),
    }


# ---------------------------------------------------------------------------
# 2. Campaign replay with configurable gates and Lyapunov threshold
# ---------------------------------------------------------------------------
def gate2_param(intent: sa.Intent, v_max: float) -> str:
    """gate2_cbf with the Lyapunov threshold as a parameter (5000 in the campaign)."""
    desired = intent.desired_state.copy()
    margins, ok = sa.compute_cbf_barriers(desired)
    if ok:
        v = float(np.sum((desired - X_REF) ** 2))
        return sa.DECISION_ACCEPT if v < v_max else sa.DECISION_DENY
    amended = desired.copy()
    if margins[0] < 0:
        amended[sa.IDX_TX_POWER] = sa.P_MAX - 1.0
    if margins[1] < 0:
        amended[sa.IDX_TX_POWER] = sa.P_MIN + 1.0
    if margins[2] < 0:
        amended[sa.IDX_PRB_UTIL] = sa.PRB_MAX - 5.0
    if margins[3] < 0:
        amended[sa.IDX_HO_HYST] = sa.H_MIN + 0.5
    _, amended_ok = sa.compute_cbf_barriers(amended)
    return sa.DECISION_AMEND if amended_ok else sa.DECISION_DENY


def replay(g1=True, g2=True, g3=True, v_max=5000.0, check=False) -> dict:
    tot = {"accepted": 0, "amended": 0, "denied": 0, "violations": 0,
           "nominal": 0, "nominal_admitted": 0, "adversarial": 0,
           "adversarial_admitted": 0}
    for run_id in range(sa.N_RUNS):
        rng = np.random.default_rng(run_id * 1000 + 42)
        last, now = -1.0, 0.0
        for _ in range(sa.N_INTENTS):
            now += rng.uniform(0.5, 3.0)
            it = sa.generate_intent(rng, now)
            d = sa.DECISION_ACCEPT
            if g1 and not sa.gate1_cue(it)[0]:
                d = sa.DECISION_DENY
            if d != sa.DECISION_DENY and g2:
                d = gate2_param(it, v_max)
                if check:
                    ref = sa.gate2_cbf(it)[0]
                    assert d == ref, "gate2_param differs from gate2_cbf"
            if d != sa.DECISION_DENY and g3 and not sa.gate3_zeno(it, last)[0]:
                d = sa.DECISION_DENY
            kind = "adversarial" if it.is_adversarial else "nominal"
            tot[kind] += 1
            if d == sa.DECISION_DENY:
                tot["denied"] += 1
            else:
                tot["accepted" if d == sa.DECISION_ACCEPT else "amended"] += 1
                tot[f"{kind}_admitted"] += 1
                last = it.timestamp
            _, safe = sa.compute_cbf_barriers(it.desired_state)
            if it.is_adversarial and d == sa.DECISION_ACCEPT and not safe:
                tot["violations"] += 1
    return tot


def tables(numbers: dict) -> None:
    full = replay(check=True)  # also proves gate2_param == gate2_cbf at v_max = 5000
    configs = [("Full DSF", True, True, True), ("Without Gate 1 (schema)", False, True, True),
               ("Without Gate 2 (CBF + Lyapunov)", True, False, True),
               ("Without Gate 3 (Zeno)", True, True, False), ("No filter", False, False, False)]
    rows = []
    for name, a, b, c in configs:
        r = full if (a, b, c) == (True, True, True) else replay(a, b, c)
        n = sa.N_RUNS * sa.N_INTENTS
        rows.append({"configuration": name, "accepted_pct": round(100 * r["accepted"] / n, 2),
                     "amended_pct": round(100 * r["amended"] / n, 2),
                     "denied_pct": round(100 * r["denied"] / n, 2),
                     "violations_total": r["violations"],
                     "violations_per_run": round(r["violations"] / sa.N_RUNS, 1)})
    with open(os.path.join(RES, "ablation.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    numbers["ablation"] = rows

    sweep = []
    for v in [100, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 5000, math.inf]:
        r = full if v == 5000 else replay(v_max=v)
        n = sa.N_RUNS * sa.N_INTENTS
        sweep.append({"v_max": "inf" if math.isinf(v) else v,
                      "admitted_pct": round(100 * (r["accepted"] + r["amended"]) / n, 2),
                      "nominal_admitted_pct": round(100 * r["nominal_admitted"] / r["nominal"], 2),
                      "adversarial_admitted_pct": round(100 * r["adversarial_admitted"] / r["adversarial"], 2),
                      "violations_total": r["violations"]})
    with open(os.path.join(RES, "vmax_sweep.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sweep[0]))
        w.writeheader()
        w.writerows(sweep)
    numbers["vmax_sweep"] = sweep
    fig_tradeoff(sweep)


def fig_tradeoff(sweep: list) -> None:
    finite = [s for s in sweep if s["v_max"] != "inf"]
    x = [s["v_max"] for s in finite]
    fig, ax = plt.subplots(figsize=(W1, 2.0))
    ax.plot(x, [s["nominal_admitted_pct"] for s in finite], color=C1, marker="o", ms=3.5,
            label="Nominal intents")
    ax.plot(x, [s["admitted_pct"] for s in finite], color=C2, marker="s", ms=3.5,
            label="All intents")
    ax.axvline(5000, color=MUTED, lw=0.8, ls="--")
    ax.text(4600, 50, "campaign\nsetting", color=MUTED, fontsize=6.5, va="center", ha="right")
    ax.set_xscale("log")
    ax.set_xlabel(r"Lyapunov admission threshold $V_{\max}$")
    ax.set_ylabel("Safe admission (%)")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", frameon=False, bbox_to_anchor=(0.86, 0.02))
    viol = sum(s["violations_total"] for s in sweep)
    ax.set_title(f"Safety violations at every threshold: {viol}", color=INK, loc="left")
    fig.savefig(os.path.join(FIG, "fig_tradeoff.pdf"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Decision breakdown from the per-run results
# ---------------------------------------------------------------------------
def fig_decisions(numbers: dict) -> None:
    with open(os.path.join(RES, "per_run.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    tot = {k: sum(int(r[k]) for r in rows) for k in rows[0] if k not in (
        "run_id", "seed", "acceptance_rate_accepted_only", "acceptance_rate_with_amended")}
    acc = np.array([float(r["acceptance_rate_accepted_only"]) for r in rows])
    adm = np.array([float(r["acceptance_rate_with_amended"]) for r in rows])
    t49 = 2.0096  # t(0.975, 49)
    numbers["campaign"] = {
        "totals": tot,
        "accepted_only_mean": round(float(acc.mean()), 6), "accepted_only_std": round(float(acc.std(ddof=1)), 6),
        "accepted_only_ci95": [round(float(acc.mean() - t49 * acc.std(ddof=1) / math.sqrt(len(acc))), 4),
                               round(float(acc.mean() + t49 * acc.std(ddof=1) / math.sqrt(len(acc))), 4)],
        "admitted_mean": round(float(adm.mean()), 6), "admitted_std": round(float(adm.std(ddof=1)), 6),
    }

    # Outcome by intent type and denial cause, from a replay of the campaign.
    by = {k: {"acc": 0, "amd": 0, "schema": 0, "lyap": 0, "other": 0}
          for k in ("Nominal", "Adversarial")}
    for run_id in range(sa.N_RUNS):
        rng = np.random.default_rng(run_id * 1000 + 42)
        last, now = -1.0, 0.0
        for _ in range(sa.N_INTENTS):
            now += rng.uniform(0.5, 3.0)
            it = sa.generate_intent(rng, now)
            k = "Adversarial" if it.is_adversarial else "Nominal"
            if not sa.gate1_cue(it)[0]:
                by[k]["schema"] += 1
                continue
            d = sa.gate2_cbf(it)[0]
            if d == sa.DECISION_DENY:
                _, ok = sa.compute_cbf_barriers(it.desired_state.copy())
                by[k]["lyap" if ok else "other"] += 1
                continue
            if not sa.gate3_zeno(it, last)[0]:
                by[k]["other"] += 1
                continue
            by[k]["acc" if d == sa.DECISION_ACCEPT else "amd"] += 1
            last = it.timestamp
    nom = sum(by["Nominal"].values())
    adv = sum(by["Adversarial"].values())
    assert nom == tot["nominal"] and adv == tot["adversarial"]
    assert by["Nominal"]["other"] == 0 and by["Adversarial"]["other"] == 0
    assert (by["Nominal"]["acc"] + by["Adversarial"]["acc"]) == tot["accepted"]
    segs = {k: [v["acc"], v["amd"], v["schema"], v["lyap"]] for k, v in by.items()}
    labels = ["Accepted unchanged", "Amended", "Rejected (Gate 1)", "Rejected (Lyapunov)"]
    colors = [C3, C1, C4, C2]
    hatches = ["", "", "////", "\\\\\\\\"]
    fig, ax = plt.subplots(figsize=(W1, 1.55))
    for yi, (name, vals) in enumerate(segs.items()):
        n = nom if name == "Nominal" else adv
        left = 0.0
        for v, lab, col, h in zip(vals, labels, colors, hatches):
            share = 100.0 * v / n
            if share <= 0:
                continue
            ax.barh(yi, share, left=left, color=col, edgecolor="white", linewidth=1.0,
                    hatch=h, label=lab if yi == 0 or lab == "Amended" else None, height=0.6)
            if share >= 10:
                ax.text(left + share / 2, yi, f"{share:.1f}", ha="center", va="center",
                        fontsize=6.5, color=INK,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
            left += share
    ax.set_yticks([0, 1], [f"Nominal\n(n={nom})", f"Adversarial\n(n={adv})"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of intents (%)")
    ax.grid(axis="y", visible=False)
    handles, labs = ax.get_legend_handles_labels()
    order = [labs.index(l) for l in labels if l in labs]
    ax.legend([handles[i] for i in order], [labs[i] for i in order], ncol=3, frameon=False,
              loc="lower center", bbox_to_anchor=(0.45, 1.0), handlelength=1.2, columnspacing=0.8)
    ax.invert_yaxis()
    fig.savefig(os.path.join(FIG, "fig_decisions.pdf"))
    plt.close(fig)
    numbers["decisions_by_type"] = {k: v for k, v in segs.items()}

    # Per-run spread and composition of the unsafe intents (for traceability).
    unsafe = unsafe_malformed = multi = 0
    base_per_run = []
    for run_id in range(sa.N_RUNS):
        rng = np.random.default_rng(run_id * 1000 + 42)
        now, b = 0.0, 0
        for _ in range(sa.N_INTENTS):
            now += rng.uniform(0.5, 3.0)
            it = sa.generate_intent(rng, now)
            m, ok = sa.compute_cbf_barriers(it.desired_state)
            if not ok:
                unsafe += 1
                multi += int(sum(1 for x in m if x < 0) > 1)
                unsafe_malformed += int(it.is_malformed)
                b += int(it.is_adversarial)
        base_per_run.append(b)
    bp = np.array(base_per_run)
    numbers["per_run_spread"] = {
        "accepted_only_min": float(acc.min()), "accepted_only_max": float(acc.max()),
        "safe_admission_min": float(adm.min()), "safe_admission_max": float(adm.max()),
        "baseline_violations_mean": round(float(bp.mean()), 2),
        "baseline_violations_std": round(float(bp.std(ddof=1)), 2),
        "baseline_violations_min": int(bp.min()), "baseline_violations_max": int(bp.max()),
    }
    numbers["unsafe_intents"] = {
        "total": unsafe, "malformed_rejected_by_gate1": unsafe_malformed,
        "reaching_gate2": unsafe - unsafe_malformed, "violating_more_than_one_barrier": multi,
        "share_of_adversarial": round(unsafe / tot["adversarial"], 4),
    }


# ---------------------------------------------------------------------------
# 4. Latency
# ---------------------------------------------------------------------------
def ecdf(a):
    a = np.sort(np.asarray(a))
    return a, np.arange(1, len(a) + 1) / len(a)


def fig_latency(numbers: dict) -> None:
    cpp = np.loadtxt(os.path.join(RES, "cpp_eval_us.csv"), delimiter=",", skiprows=1)
    py = np.genfromtxt(os.path.join(RES, "python_gate_latency.csv"), delimiter=",",
                       skip_header=1, usecols=(1, 2))
    wall_us, rep_us = py[:, 0] * 1000.0, py[:, 1] * 1000.0
    fig, ax = plt.subplots(figsize=(W1, 1.9))
    for data, col, lab in ((cpp, C1, "C++ core: 4 barriers + Lyapunov"),
                           (wall_us, C3, "Python gates: measured wall clock"),
                           (rep_us, C2, "Python campaign: reported value")):
        x, y = ecdf(data)
        ax.plot(x, y, color=col, label=lab)
    ax.set_xscale("log")
    ax.set_xlabel(r"Latency per intent ($\mu$s, log scale)")
    ax.set_ylabel("ECDF")
    ax.set_ylim(0, 1.02)
    ax.legend(loc="upper center", frameon=False, bbox_to_anchor=(0.5, -0.3), ncol=1)
    fig.savefig(os.path.join(FIG, "fig_latency.pdf"))
    plt.close(fig)

    def st(a):
        return {"mean": round(float(np.mean(a)), 3), "median": round(float(np.median(a)), 3),
                "p99": round(float(np.percentile(a, 99)), 3), "n": int(len(a))}
    numbers["latency_us"] = {"cpp_core": st(cpp), "python_wall": st(wall_us),
                             "python_reported": st(rep_us)}


def main() -> None:
    numbers: dict = {}
    fig_telemetry(numbers)
    fig_decisions(numbers)
    tables(numbers)
    fig_latency(numbers)
    with open(os.path.join(RES, "paper_numbers.json"), "w", encoding="utf-8") as f:
        json.dump(numbers, f, indent=2)
    print(json.dumps(numbers, indent=2))


if __name__ == "__main__":
    main()
