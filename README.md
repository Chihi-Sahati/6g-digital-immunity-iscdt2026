# ISCDT 2026 companion code: Deterministic Digital Immunity (conference version)

This repository holds the code behind the ISCDT 2026 paper *"Deterministic Digital
Immunity for Software-Defined 6G Networks via Control Barrier Functions and Lyapunov
Stability"* (accepted for oral presentation, Benghazi, 21-23 November 2026).

It is separate from the IEEE TNSM code base (`Chihi-Sahati/6g-digital-immunity`). The
conference state is tagged:

- `snapshot-996c6c0`: exact archive of commit 996c6c0 of the TNSM repository (the code used
  for the conference paper, unchanged).
- `iscdt-2026-v1`: first revision (C++ fixes, unit tests, documentation). Does not build
  on Ubuntu because of the Eigen version check; superseded.
- `iscdt-2026-v1.1`: builds in CI, per-run results. Contains the generator error
  described in `ERRATUM.md`; superseded.
- `iscdt-2026-v1.2`: current reference version. Generator error fixed, all results
  regenerated, latency benchmarks and the figure script added. Cite this tag.

## Scope

| Item | This repository (conference) | TNSM repository (journal) |
|---|---|---|
| Safety filter | C++20 CBF core (`safety-filter/core/cbf_math.cpp`); the campaign uses a Python implementation of the same box barriers | Python DCBF-QP with trust region |
| Plant | Single cell, 140 GHz (Sub-THz) | 19-cell hexagonal RAN, 7 GHz, 3GPP TR 38.901 UMa |
| Barriers | Linear box barriers on configuration parameters | Configuration box plus nonlinear KPI barriers |
| Lyapunov | Static threshold V < 5000 in the campaign; decrease condition in the C++ core | Discrete-time formulation |
| Intent generator | Synthetic generator `generate_intent()` in `evaluation/statistical_analysis.py` | LLM fault model |

## Documentation

- `ASSUMPTIONS.md`: assumptions under which the safety claims hold (reviewer comment 2).
- `LIMITATIONS.md`: simulation-versus-reality discussion (reviewer comment 1).
- `INTENT_MAPPING.md`: intent format, gate logic and the intent generator (comments 3 and 4).
- `RESULTS.md` and `evaluation/results/`: reproduced numbers and decision breakdown (comment 3).
- `RELEASE.md`: what is released (comment 4).
- `CPP_STATUS.md`: state of the C++ core, its fixes and tests.
- `ERRATUM.md`: the generator error fixed in v1.2 and its effect.

## Changes to the snapshot code

- `safety-filter/core/cbf_math.hpp`: missing `#include <iomanip>` added.
- `safety-filter/core/cbf_math.cpp`: a control vector of the wrong size now fails closed.
- `safety-filter/CMakeLists.txt`: Eigen 3.4 or newer accepted; `-march=native` is opt-in.
- `safety-filter/core/zeno_guard.py`: default tau_min 0.2 s (was 0.5 s), matching the
  campaign and the paper; docstring scope note.
- New: `tests/test_cbf_core_cpp.cpp`, `evaluation/acceptance_breakdown.py`,
  `evaluation/campaign_details.py`, `.github/workflows/cpp-core.yml`.

- `evaluation/statistical_analysis.py`: nominal-intent generator fixed (`ERRATUM.md`);
  everything else in the campaign is unchanged.
- New in v1.2: `evaluation/paper_figures.py`, `evaluation/bench_python_gates.py`,
  `tests/bench_cbf_core.cpp`, `evaluation/figures/`, and the results listed in `RESULTS.md`.

## How to run

    # Campaign (Python 3, numpy, scipy, matplotlib)
    python3 evaluation/statistical_analysis.py
    python3 evaluation/campaign_details.py

    # C++ core (CMake, a C++20 compiler, Eigen 3.4 or newer)
    cmake -S safety-filter -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_PYTHON_BINDINGS=OFF
    cmake --build build
    g++ -std=c++20 -Isafety-filter/core -I<eigen-include> tests/test_cbf_core_cpp.cpp build/libcbf_core.a -o test_cbf_core
    ./test_cbf_core

## Continuous integration

The workflow `.github/workflows/cpp-core.yml` builds the C++ core with CMake and runs
`tests/test_cbf_core_cpp.cpp` on Ubuntu 24.04, and runs `tests/test_zeno_guard.py` with
pytest. The Python reproduction scripts in
`evaluation/` are not part of CI; they are run manually as described in `RESULTS.md`.

## Legacy scripts from the snapshot

`evaluation/generate_mdpi_figures.py` draws illustrative curves for an earlier manuscript;
its figures are not simulation output. `evaluation/ablation_study.py` and
`evaluation/sensitivity_analysis.py` use their own intent generators and are not the source
of the current results. Their outputs, and the earlier manuscript figures, are no longer
kept in this repository; they remain available in tag `snapshot-996c6c0`. Current results
come from `statistical_analysis.py`, `campaign_details.py`, `paper_figures.py` and the two
benchmarks (see `RESULTS.md`).

