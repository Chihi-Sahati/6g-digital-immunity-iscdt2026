# Status of the C++ core

Reviewers asked about the "C++ Deterministic Safety Filter" that the paper describes.
This is what the repository contains and what the evaluation actually uses.

## What exists

- `safety-filter/core/cbf_math.hpp` (462 lines) and `cbf_math.cpp` (498 lines), in
  commit 996c6c0 and in this repository. They define `CbfEngine`, `CbfResult`,
  `LyapunovResult`, `NetworkState`, `BarrierFunction` and `LyapunovConfig`.
- The build file `safety-filter/CMakeLists.txt` (C++20, Eigen3 required, pybind11
  optional) and `requirements-cpp.txt`.
- `safety-filter/core/cbf_engine.py` loads `libcbf_core.so` through ctypes.

## What the evaluation uses

- The 50-run campaign (`evaluation/statistical_analysis.py`) is pure Python. It does not
  import ctypes, pybind11 or the shared library. Its barrier checks and Lyapunov check
  are written in Python.
- The ablation study (`evaluation/ablation_study.py`) is also pure Python.
- No evaluation script calls the C++ core. Only the unit test `tests/test_cbf_core_cpp.cpp` does.

## What was checked

- Eigen 3.4.0 installed at C:\eigen-3.4.0 (headers only).
- `cbf_math.cpp` compiles with `g++ -std=c++20 -Wall -Wextra -c` against Eigen 3.4.0 with
  0 errors and 0 warnings, on GCC 11.4 (Ubuntu 22.04).
- The first attempt failed because `cbf_math.hpp` used `std::put_time`, `std::setw`,
  `std::setfill` and `std::setprecision` without `#include <iomanip>`. GCC does not include
  it transitively. The include was added in this repository only. No logic was changed.
- Unit test: `tests/test_cbf_core_cpp.cpp`, 8 checks. A defect found by the first version
  of the test (a control vector of the wrong size silently disabled the control term) has
  been fixed; see "Fix applied" below. All 8 checks pass.
- The 1.56 ms latency in the submitted paper is the Python latency of the simulation (see
  `LIMITATIONS.md`, item 6). It is not a latency of the C++ core.

## What remains open

1. The campaign does not call the C++ core. Either wire it in through `cbf_engine.py` and
   re-run, or describe the campaign as a Python reference implementation of the barriers.
2. Latency is now measured by `tests/bench_cbf_core.cpp`: 0.30 us mean, 0.37 us p99 per
   evaluation of four barriers and the Lyapunov condition (100,000 evaluations, -O2,
   Intel Core Ultra 7 255H in a Linux VM). The Python gate pipeline takes 17 us mean
   (`evaluation/bench_python_gates.py`). The 1.56 ms figure is not a C++ latency.

## Build and test on Windows (24 October 2026)

- Toolchain: MSYS2 UCRT64, GCC 16.2.0, CMake 4.4.4, Eigen 5.0.1 (pacman package
  `mingw-w64-ucrt-x86_64-eigen3`). The package does not provide Eigen 3.4, so
  `safety-filter/CMakeLists.txt` was changed to `find_package(Eigen3 3.4...<6 ...)`.
  Eigen 5 has not been tested beyond this build and test.
- `cmake -S safety-filter -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_PYTHON_BINDINGS=OFF`
  and `cmake --build build` succeed, producing `build/libcbf_core.a`.
- `tests/test_cbf_core_cpp.cpp` compiled against `cbf_math.cpp` and run: 4 PASS, 2 FAIL.
  The two failures are the known defect described above (dimension mismatch silently
  disables the control term). Test output is shown correctly in a UTF-8 console; the
  mojibake in logs comes from the console code page, not from the code.
- Running the test binary linked against `build/libcbf_core.a` returned exit code 127 in
  MSYS2 and produced no output. The same test compiled directly from source ran normally.
  The cause is not yet identified.

## Fix applied: control-dimension mismatch now fails closed (24 October 2026, approved)

- Before: a control vector whose size differed from state_dim only logged a warning and set
  the control term to zero, so an action that crossed the ceiling could pass.
- After: `cbf_math.cpp` throws inside the per-barrier evaluation, and the existing per-barrier
  handler reports that barrier as not passed with margin -inf. The error is logged. The
  header documents this behaviour.
- Test `tests/test_cbf_core_cpp.cpp`: all 8 checks pass on GCC 11.4 (Ubuntu) and
  GCC 16.2 (MSYS2 UCRT64, same source). This supersedes the earlier "4 PASS, 2 FAIL" result.
- Still open: the exit-127 issue when running the test linked against `build/libcbf_core.a`.

## Resolved: exit code 127 with the CMake-built library (24 October 2026)

- Cause: `-march=native` in the Release flags of `safety-filter/CMakeLists.txt`. A test
  linked against a library compiled with it exited with 127 and no output on the build
  machine. Compiling the same source without it works.
- Fix: Release now uses `-O2` only. `-march=native` is opt-in via `-DCBF_MARCH_NATIVE=ON`.
- Verified: CMake build with `-DCMAKE_BUILD_TYPE=Release` and the test linked against
  `build/libcbf_core.a` print `ALL TESTS PASSED` with exit code 0 on MSYS2 UCRT64.
