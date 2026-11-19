// tests.cpp - verifica el Virtual Tree contra una definición por fuerza bruta.
// g++ -std=c++17 -O2 tests.cpp -o tests && ./tests
#include <iostream>
#include <set>
#include <random>
#include "virtual_tree.hpp"
using namespace std;

static int naive_lca(const RootedTree& t, int a, int b) {
    while (t.depth[a] > t.depth[b]) a = t.par[a];
    while (t.depth[b] > t.depth[a]) b = t.par[b];
    while (a != b) { a = t.par[a]; b = t.par[b]; }
    return a;
}

// Definición: V' = cierre de S bajo LCA; padre virtual = ancestro propio más cercano en V'.
static void expected(const RootedTree& t, const vector<int>& q,
                     set<int>& S, set<pair<int,int>>& E) {
    set<int> Q(q.begin(), q.end());
    S = Q;
    for (int a : Q) for (int b : Q) S.insert(naive_lca(t, a, b));
    E.clear();
    for (int v : S) {
        int p = t.par[v];
        while (p != -1 && !S.count(p)) p = t.par[p];
        if (p != -1) E.insert({p, v});
    }
}

static bool matches(const VTResult& r, const set<int>& S, const set<pair<int,int>>& E, size_t k) {
    set<int> got(r.nodes.begin(), r.nodes.end());
    set<pair<int,int>> gotE(r.edges.begin(), r.edges.end());
    return got == S && gotE == E
        && got.size() == r.nodes.size()               // sin nodos repetidos
        && r.nodes.size() <= 2 * k - 1                // cota 2k - 1
        && r.edges.size() + 1 == r.nodes.size();      // es un árbol
}

int main() {
    mt19937 rng(12345);
    const int trials = 3000;
    for (int it = 0; it < trials; ++it) {
        int n = 1 + rng() % 40;
        vector<pair<int,int>> edges;
        for (int i = 1; i < n; ++i) edges.push_back({(int)(rng() % i), i});
        RootedTree t(n, edges, 0);

        int k = 1 + rng() % n;
        vector<int> q;
        for (int i = 0; i < k; ++i) q.push_back(rng() % n);      // con duplicados

        set<int> S; set<pair<int,int>> E;
        expected(t, q, S, E);
        size_t kk = set<int>(q.begin(), q.end()).size();

        if (!matches(t.build_virtual(q), S, E, kk)) {
            cout << "FALLO build_virtual en intento " << it << "\n"; return 1;
        }
        // Variante O(k): se le pasa la consulta ya ordenada por tin y sin duplicados
        set<int> uq(q.begin(), q.end());
        vector<int> qs(uq.begin(), uq.end());
        sort(qs.begin(), qs.end(), [&](int a, int b) { return t.tin[a] < t.tin[b]; });
        if (!matches(t.build_virtual_sorted(qs), S, E, kk)) {
            cout << "FALLO build_virtual_sorted en intento " << it << "\n"; return 1;
        }
    }

    // Caso borde: consulta vacía
    RootedTree t1(1, {}, 0);
    VTResult e1 = t1.build_virtual({}), e2 = t1.build_virtual_sorted({});
    if (!e1.nodes.empty() || !e1.edges.empty() || !e2.nodes.empty() || !e2.edges.empty()) {
        cout << "FALLO vacío\n"; return 1;
    }

    // Caso borde: cadena de 10^6 nodos (DFS iterativo, sin desbordar la pila)
    const int N = 1000000;
    vector<pair<int,int>> chain;
    for (int i = 1; i < N; ++i) chain.push_back({i - 1, i});
    RootedTree tc(N, chain, 0);
    VTResult rc = tc.build_virtual({N - 1, 0, N / 2});
    if (rc.nodes.size() != 3 || rc.edges.size() != 2 || tc.lca(N - 1, N / 3) != N / 3) {
        cout << "FALLO cadena\n"; return 1;
    }

    cout << "OK: " << trials << " casos aleatorios x 2 variantes + caso vacío"
         << " + cadena de " << N << " nodos\n";
    return 0;
}
