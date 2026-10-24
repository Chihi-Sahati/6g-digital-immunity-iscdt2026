# ISCDT 2026 companion code: Deterministic Digital Immunity (conference version)

This repository holds the code behind the ISCDT 2026 paper *"Deterministic Digital
Immunity for Software-Defined 6G Networks via Control Barrier Functions and Lyapunov
Stability"* (accepted for oral presentation, Benghazi, 21-23 November 2026).

It is separate from the IEEE TNSM code base (`Chihi-Sahati/6g-digital-immunity`). The
conference state is tagged:

- `snapshot-996c6c0`: exact archive of commit 996c6c0 of the TNSM repository (the code used
  for the conference paper, unchanged).
- `iscdt-2026-v1`: the same code with the revisions listed in the commit message (C++ fixes,
  build changes, unit tests, documentation).

## Scope

| Item | Conference version (this folder) | Journal version (repository root) |
|---|---|---|
| Safety filter | C++20 CBF core (`safety-filter/core/cbf_math.cpp`) with Python ctypes wrapper | Python DCBF-QP with trust region (`safety-filter/core/ddi_filter.py`) |
| Plant | Single cell, 140 GHz (Sub-THz) | 19-cell hexagonal RAN, 7 GHz, 3GPP TR 38.901 UMa |
| Barriers | Linear box barriers on configuration parameters | Configuration box plus nonlinear KPI barriers (load, edge SINR) |
| Time model | Continuous-time CBF with Lyapunov condition, sampled at the actuation rate | Discrete-time CBF (DCBF) |
| Intent generator | Rule-based `llm-agent/intent/config_generator.py` | Fault model `simulation/llm_intent_model.py` |

## Files added on top of the snapshot

- `README.md`: this file.
- `REVIEW_RESPONSE.md`: point-by-point response to the committee's MINOR REVISION report.
- `ASSUMPTIONS.md`: the modelling assumptions under which the "guarantee" language holds (reviewer comment 2).
- `LIMITATIONS.md`: simulation-versus-reality discussion (reviewer comment 1).
- `INTENT_MAPPING.md`: how an intent becomes a CBF constraint and what the LLM contributes (reviewer comment 4).
- `RELEASE.md`: what is and is not released, and under which terms (reviewer comment 4).

No source logic was changed. The only code edit is a clarifying note in the docstring of
`safety-filter/core/zeno_guard.py`, so that the numbers reported in the paper remain
reproducible from this exact code.

## How to run (as in the original commit)

See the original `docs/REPRODUCIBILITY.md` in this folder and `README.md` of the snapshot
for Docker and unit-test instructions. The C++ core must be built from `safety-filter/`
before the Python wrapper can use it (`CMakeLists.txt`).
