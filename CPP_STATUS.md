# Status of the C++ core

Reviewers asked about the "C++ Deterministic Safety Filter" that the paper describes.
This is what the repository contains and what the evaluation actually uses.

## What exists

- `safety-filter/core/cbf_math.hpp` (462 lines) and `cbf_math.cpp` (498 lines), in
  commit 996c6c0 and in this folder. They define `CbfEngine`, `CbfResult`,
  `LyapunovResult`, `NetworkState`, `BarrierFunction` and `LyapunovConfig`.
- The build file `safety-filter/CMakeLists.txt` (C++20, Eigen3 required, pybind11
  optional) and `requirements-cpp.txt`.
- `safety-filter/core/cbf_engine.py` loads `libcbf_core.so` through ctypes.

## What the evaluation uses

- The 50-run campaign (`evaluation/statistical_analysis.py`) is pure Python. It does not
  import ctypes, pybind11 or the shared library. Its barrier checks and Lyapunov check
  are written in Python.
- The ablation study (`evaluation/ablation_study.py`) is also pure Python.
- No test or script in this folder calls the C++ core.

## What was checked

- Eigen 3.4.0 installed at C:\eigen-3.4.0 (headers only).
- `cbf_math.cpp` compiles with `g++ -std=c++20 -Wall -Wextra -c` against Eigen 3.4.0 with
  0 errors and 0 warnings, on GCC 11.4 (Ubuntu 22.04).
- The first attempt failed because `cbf_math.hpp` used `std::put_time`, `std::setw`,
  `std::setfill` and `std::setprecision` without `#include <iomanip>`. GCC does not include
  it transitively. The include was added in this folder only. No logic was changed.
- Unit test: `tests/test_cbf_core_cpp.cpp` (build command in the file header). Six checks:
  the first four pass (safe state passes, h(x) is correct, unsafe state is rejected, an
  action that crosses the ceiling is rejected), and the last two FAIL. This is a real defect:
  - `evaluate_all_barriers()` documents `@throws std::invalid_argument` on a dimension
    mismatch, but when the control vector has the wrong length it only logs a warning and
    sets the control term L_g*h*u to zero.
  - Consequence: with a malformed 2-element control, an action that crosses the power ceiling
    passes the barrier (margin -0.97 becomes +0.03).
  - The defect is not in the Python campaign (which does not call this code), but it is in
    the C++ core that the paper describes. It must be fixed before the paper claims a C++
    safety filter. The fix is a one-line change (throw instead of warn), and needs your approval
    because it changes the core's behaviour.
- CMake was not run: CMake is not installed on the device VM, so the build used g++ directly.
- The 1.56 ms latency in the paper is the Python latency of the simulation (see
  `LIMITATIONS.md`, item 6). It is not a latency of the C++ core.

## What must be done before the paper claims a C++ result

1. Build the library with `cmake` as described in `CMakeLists.txt` (the compile step is
   already confirmed), and add a unit test for `CbfEngine`.
2. Either wire the campaign to the C++ core through `cbf_engine.py` and re-run it, or
   state clearly in the paper that the campaign uses a Python reference implementation of
   the same barrier equations. Do not present the Python latency as C++ latency.
3. Report the latency of the C++ core separately, measured on a stated machine.

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
