// Unit test for the ISCDT 2026 C++ CBF core (safety-filter/core/cbf_math.cpp).
// Build and run from the iscdt-2026 folder, with <eigen> = the Eigen 3.4.0 folder:
//   g++ -std=c++20 -Wall -Wextra -Isafety-filter/core -I<eigen> tests/test_cbf_core_cpp.cpp safety-filter/core/cbf_math.cpp -o test_cbf_core
//   ./test_cbf_core
// Tests 5 and 6 cover the fix that makes a control-vector dimension mismatch throw
// instead of silently zeroing the control term. See CPP_STATUS.md.
#include "cbf_math.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>

using namespace cbf::core;

static int failures = 0;

static void check(bool ok, const char* name) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << "\n";
    if (!ok) ++failures;
}

// Barrier h(x) = 43 - x0 (transmit-power ceiling), gamma(h) = 0.3 * h.
static BarrierFunction power_ceiling() {
    BarrierFunction b;
    b.id = "tx_power_ceiling";
    b.h = [](const Eigen::VectorXd& x) { return 43.0 - x(0); };
    b.grad_h = [](const Eigen::VectorXd&) {
        Eigen::RowVectorXd g(3);
        g << -1.0, 0.0, 0.0;
        return g;
    };
    b.gamma = [](double h) { return 0.3 * h; };
    b.expr = "h(x) = 43 - tx_power >= 0";
    return b;
}

static NetworkState state_with(double tx_power) {
    NetworkState s;
    s.x = Eigen::VectorXd(3);
    s.x << tx_power, 3.0, 50.0;
    return s;
}

int main() {
    CbfEngine engine(3);
    engine.add_barrier(power_ceiling());

    Eigen::VectorXd no_action = Eigen::VectorXd::Zero(3);

    // 1. Safe state, zero control: margin = gamma(h) = 0.3 * 3 = 0.9 >= 0.
    auto safe = engine.evaluate_all_barriers(state_with(40.0), no_action);
    check(safe.size() == 1 && safe[0].passed, "safe state passes");
    check(std::abs(safe[0].cbf_value - 3.0) < 1e-12, "h(x) evaluated correctly");

    // 2. Already unsafe state (tx_power 50 dBm > 43): must fail.
    auto unsafe = engine.evaluate_all_barriers(state_with(50.0), no_action);
    check(!unsafe[0].passed, "unsafe state is rejected");
    check(unsafe[0].margin < 0.0, "unsafe state has negative margin");

    // 3. Near the boundary (h = 0.1) with a control that pushes power up (u0 = +1):
    //    margin = L_g h * u + gamma(h) = -1 + 0.03 < 0, so the action must be rejected.
    Eigen::VectorXd push_up = Eigen::VectorXd::Zero(3);
    push_up(0) = 1.0;
    auto near_push = engine.evaluate_all_barriers(state_with(42.9), push_up);
    check(!near_push[0].passed, "action that crosses the ceiling is rejected");

    // 4. Same state with a control that lowers power: must pass.
    Eigen::VectorXd push_down = Eigen::VectorXd::Zero(3);
    push_down(0) = -1.0;
    auto near_drop = engine.evaluate_all_barriers(state_with(42.9), push_down);
    check(near_drop[0].passed, "action that lowers power at the boundary passes");

    // 5. Dimension mismatch fails closed: the barrier is reported as not passed.
    Eigen::VectorXd wrong(2);
    wrong << 0.0, 0.0;
    auto mismatch = engine.evaluate_all_barriers(state_with(40.0), wrong);
    check(!mismatch[0].passed, "dimension mismatch fails closed (barrier not passed)");

    // 6. Consequence of the defect: with a malformed 2-D control, an action that would
    //    cross the ceiling (u0 = +1 at h = 0.1) is wrongly accepted.
    Eigen::VectorXd bad_u(2);
    bad_u << 1.0, 0.0;
    auto defect = engine.evaluate_all_barriers(state_with(42.9), bad_u);
    check(!defect[0].passed, "malformed control cannot bypass the barrier ");

    std::cout << (failures == 0 ? "ALL TESTS PASSED" : "SOME TESTS FAILED") << "\n";
    return failures == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
