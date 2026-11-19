// bench.cpp - medición empírica del Virtual Tree.
// g++ -std=c++17 -O2 bench.cpp -o bench && ./bench
//
// Experimento 1: k fijo (100), n creciente -> el costo por consulta no depende de n.
// Experimento 2: n fijo (10^6), k creciente -> build_virtual crece como k log k y
//                build_virtual_sorted (entrada ya ordenada) como k.
// Referencia: un recorrido completo O(n) del árbol, que es lo que costaría
// resolver cada consulta sin comprimir.
#include <chrono>
#include <cstdio>
#include <random>
#include <numeric>
#include "virtual_tree.hpp"
using namespace std;
using Clock = chrono::steady_clock;

static RootedTree random_tree(int n, mt19937& rng) {
    vector<pair<int,int>> e;
    e.reserve(n);
    for (int i = 1; i < n; ++i) e.push_back({(int)(rng() % i), i});
    return RootedTree(n, e, 0);
}

static vector<int> sample(int n, int k, mt19937& rng) {
    vector<int> q(k);
    for (int& x : q) x = rng() % n;
    return q;
}

// microsegundos promedio por consulta
template <class F> static double time_us(int reps, F f) {
    auto t0 = Clock::now();
    for (int r = 0; r < reps; ++r) f(r);
    return chrono::duration<double, micro>(Clock::now() - t0).count() / reps;
}

static volatile long long sink = 0;

static double full_scan_us(const RootedTree& t, int reps) {
    return time_us(reps, [&](int) {                   // O(n): visita todos los nodos
        long long s = 0;
        for (int v = 0; v < t.n; ++v) s += t.depth[v] + (int)t.children[v].size();
        sink += s;
    });
}

int main() {
    mt19937 rng(2026);

    printf("# Experimento 1: k = 100, n variable\n");
    printf("n,us_build_virtual,us_recorrido_completo\n");
    for (int n : {1000, 10000, 100000, 1000000}) {
        RootedTree t = random_tree(n, rng);
        const int Q = 2000;
        vector<vector<int>> qs(Q);
        for (auto& q : qs) q = sample(n, 100, rng);
        double a = time_us(Q, [&](int r) { sink += t.build_virtual(qs[r]).nodes.size(); });
        double b = full_scan_us(t, 50);
        printf("%d,%.2f,%.2f\n", n, a, b);
    }

    printf("\n# Experimento 2: n = 1000000, k variable\n");
    printf("k,us_build_virtual,us_build_virtual_sorted,nodos_promedio\n");
    const int N = 1000000;
    RootedTree t = random_tree(N, rng);
    for (int k : {10, 100, 1000, 10000, 100000}) {
        int Q = max(20, 2000000 / k / 10);
        vector<vector<int>> qs(Q), sorted(Q);
        for (int i = 0; i < Q; ++i) {
            qs[i] = sample(N, k, rng);
            sorted[i] = qs[i];
            sort(sorted[i].begin(), sorted[i].end(), [&](int a, int b) { return t.tin[a] < t.tin[b]; });
            sorted[i].erase(unique(sorted[i].begin(), sorted[i].end()), sorted[i].end());
        }
        long long tot = 0;
        double a = time_us(Q, [&](int r) { auto res = t.build_virtual(qs[r]); tot += res.nodes.size(); });
        double b = time_us(Q, [&](int r) { sink += t.build_virtual_sorted(sorted[r]).nodes.size(); });
        printf("%d,%.2f,%.2f,%.1f\n", k, a, b, (double)tot / Q);
    }
    return 0;
}
