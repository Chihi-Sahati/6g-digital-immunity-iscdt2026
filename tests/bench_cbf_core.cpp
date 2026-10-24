// Latency benchmark for the ISCDT 2026 C++ CBF core (safety-filter/core/cbf_math.cpp).
//
// Evaluates the four box barriers of the campaign (h1 = 43 - P_tx, h2 = P_tx,
// h3 = 100 - PRB, h4 = H_HO) and the Lyapunov condition V_dot <= -alpha V with
// V = ||x - x_ref||^2, x_ref = (30, 3, 50), alpha = 0.1, on random states and actions.
//
// Build (logging disabled so that log output is not timed):
//   g++ -std=c++20 -O2 -DCBF_LOG_LEVEL=0 -Isafety-filter/core -I<eigen> tests/bench_cbf_core.cpp safety-filter/core/cbf_math.cpp -o bench_cbf_core
// Run:
//   ./bench_cbf_core [n_eval] [samples.csv]
#include "cbf_math.hpp"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>
#include <vector>

using namespace cbf::core;

static BarrierFunction box(const char* id, int idx, double sign, double offset) {
    // h(x) = offset + sign * x_idx
    BarrierFunction b;
    b.id = id;
    b.h = [=](const Eigen::VectorXd& x) { return offset + sign * x(idx); };
    b.grad_h = [=](const Eigen::VectorXd&) {
        Eigen::RowVectorXd g = Eigen::RowVectorXd::Zero(3);
        g(idx) = sign;
        return g;
    };
    b.gamma = [](double h) { return 0.3 * h; };
    b.expr = id;
    return b;
}

int main(int argc, char** argv) {
    const int n_eval = argc > 1 ? std::atoi(argv[1]) : 100000;
    const char* csv = argc > 2 ? argv[2] : nullptr;

    // State order follows the campaign: (P_tx, H_HO, PRB).
    CbfEngine engine(3);
    engine.add_barrier(box("tx_power_ceiling", 0, -1.0, 43.0));
    engine.add_barrier(box("tx_power_floor", 0, 1.0, 0.0));
    engine.add_barrier(box("prb_ceiling", 2, -1.0, 100.0));
    engine.add_barrier(box("hysteresis_floor", 1, 1.0, 0.0));

    LyapunovConfig lc;
    lc.alpha = 0.1;
    lc.x_ref = Eigen::Vector3d(30.0, 3.0, 50.0);
    lc.V = [](const Eigen::VectorXd& x, const Eigen::VectorXd& r) { return (x - r).squaredNorm(); };
    lc.dVdt = [](const Eigen::VectorXd& x, const Eigen::VectorXd& r, const Eigen::VectorXd& u) {
        return 2.0 * (x - r).dot(u);
    };
    engine.set_lyapunov(lc);

    std::mt19937_64 rng(42);
    std::uniform_real_distribution<double> tx(10.0, 40.0), hy(0.5, 6.0), prb(10.0, 85.0);
    std::uniform_real_distribution<double> dtx(-5.0, 12.0), dhy(-3.0, 3.0), dprb(-20.0, 30.0);

    auto make = [&]() {
        NetworkState s;
        s.x = Eigen::Vector3d(tx(rng), hy(rng), prb(rng));
        Eigen::VectorXd u = Eigen::Vector3d(dtx(rng), dhy(rng), dprb(rng));
        return std::make_pair(s, u);
    };

    volatile double sink = 0.0;
    for (int i = 0; i < 2000; ++i) {  // warm-up
        auto [s, u] = make();
        auto r = engine.evaluate_all_barriers(s, u);
        auto l = engine.evaluate_lyapunov(s, u);
        sink = sink + r[0].margin + l.dV;
    }

    std::vector<double> us(n_eval);
    int unsafe = 0;
    for (int i = 0; i < n_eval; ++i) {
        auto [s, u] = make();
        const auto t0 = std::chrono::steady_clock::now();
        auto r = engine.evaluate_all_barriers(s, u);
        auto l = engine.evaluate_lyapunov(s, u);
        const auto t1 = std::chrono::steady_clock::now();
        bool ok = l.passed;
        for (const auto& b : r) ok = ok && b.passed;
        unsafe += ok ? 0 : 1;
        sink = sink + r[0].margin + l.dV;
        us[i] = std::chrono::duration<double, std::micro>(t1 - t0).count();
    }

    std::vector<double> sorted = us;
    std::sort(sorted.begin(), sorted.end());
    double mean = 0.0;
    for (double v : us) mean += v;
    mean /= n_eval;
    auto pct = [&](double p) { return sorted[static_cast<size_t>(p * (n_eval - 1))]; };

    std::cout << "evaluations      : " << n_eval << "\n"
              << "rejected (any)   : " << unsafe << "\n"
              << "mean   [us]      : " << mean << "\n"
              << "median [us]      : " << pct(0.50) << "\n"
              << "p99    [us]      : " << pct(0.99) << "\n"
              << "max    [us]      : " << sorted.back() << "\n";

    if (csv) {
        std::ofstream f(csv);
        f << "eval_us\n";
        for (int i = 0; i < n_eval; ++i) f << us[i] << "\n";
    }
    return sink == 12345.678 ? 1 : 0;
}
