# Limitations and the simulation-to-reality gap

This document answers reviewer comment 1 of the ISCDT 2026 committee.

1. **No standards-compliant testbed.** The results come from a simulator in which the
   RAN dynamics are Ornstein-Uhlenbeck processes. There is no measurement on
   hardware and no conformance test against a 3GPP-compliant 6G stack. The
   single-cell experiments use a 140 GHz carrier and the path-loss penalty is a
   closed-form FSPL term (about 32 dB relative to 3.5 GHz). Real Sub-THz channels also
   have blockage and atmospheric effects that are not modelled in the conference version.

2. **Latency transfer.** The sub-1.6 ms DSF latency is a wall-clock measurement of the
   filter code on the test machine. It excludes network round trips to the OsmoBTS
   or the O-RAN control plane. Real deployments add those delays, and the latency
   budget must be measured end to end before any deployment claim is made.

3. **LLM realism.** The intent generator in this version is rule-based
   (`llm-agent/intent/config_generator.py`). Its failure modes are therefore a model of
   LLM failures, not a measurement of a particular LLM. Section 2 of
   `INTENT_MAPPING.md` describes this in more detail.

4. **Unofficial LLM access in the demo path.** The repository's `llm-agent` uses the
   `g4f` library for demonstration, which relies on unofficial endpoints and is not
   suitable for production (see the snapshot README). The paper's results do not depend
   on that path, but readers who try the demo will see it.

5. **Statistical scope.** The paper reports 50 independent runs. Each run is a seeded
   simulation. The results do not cover a long-horizon deployment, multi-operator
   interference, or adversarial inputs beyond the fault model in the simulator.

6. **The 50-run campaign is a synthetic Monte Carlo study, not a system test.** Verified
   against `evaluation/statistical_analysis.py`:
   - Intents are drawn from uniform distributions (`generate_intent`), with 30 percent
     adversarial and 8 percent malformed intents set by constants. The 49.36 percent
     acceptance rate follows from these constants and the barrier bounds, not from any
     language model.
   - The barrier checks, the Lyapunov check and the amendment rule are implemented in
     Python inside that script (`compute_cbf_barriers`, `gate2_cbf`). The C++ core
     (`safety-filter/core/cbf_math.cpp`) is not called by it. See `CPP_STATUS.md`.
   - The DSF latency is the measured Python run time plus a `np.random.uniform` term
     added in each gate, so it is not a pure measurement of the filter.
   - Zero safety violations and zero Zeno violations are not independent tests. The
     amendment step clamps values into the feasible set, and the Zeno gap is larger than
     the guard interval by construction (see `ASSUMPTIONS.md`, section 5).
