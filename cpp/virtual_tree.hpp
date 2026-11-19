// virtual_tree.hpp
// Implementación propia de Virtual Tree (Auxiliary Tree) - CS2023 UTEC.
// Dado un árbol enraizado y un subconjunto de k nodos, construye el árbol
// comprimido que contiene esos nodos + los LCA necesarios (<= 2k-1 nodos).
//
// Preprocesamiento: DFS iterativo (tin/tout) + Euler tour + Sparse Table
//                   => LCA en O(1), O(n log n) tiempo y memoria.
// build_virtual        : consulta en cualquier orden y con duplicados, O(k log k).
// build_virtual_sorted : consulta ya ordenada por tin y sin duplicados, O(k).
// No se usa ninguna implementación externa de la estructura.
#pragma once
#include <vector>
#include <algorithm>
#include <utility>

struct VTStep {                 // un paso del algoritmo de la pila
    int node;                   // nodo procesado
    std::vector<int> popped;    // nodos sacados de la pila
    int parent;                 // padre virtual (-1 si es la raíz virtual)
    std::vector<int> stack;     // pila después del paso (base -> tope)
};

struct VTTrace {                // traza real de la ejecución (para la animación)
    std::vector<int> sorted_query;                    // consulta ordenada por tin
    struct Lca { int a, b, l; };
    std::vector<Lca> lcas;                            // LCA de pares adyacentes
    std::vector<int> all_nodes;                       // consulta + LCAs, por tin
    std::vector<VTStep> steps;
};

struct VTResult {
    std::vector<int> nodes;                           // ordenados por tin
    std::vector<std::pair<int,int>> edges;            // (padre, hijo)
};

class RootedTree {
public:
    int n;
    std::vector<int> tin, tout, depth, par, first;
    std::vector<std::vector<int>> children;           // en orden del DFS

    RootedTree(int n_, const std::vector<std::pair<int,int>>& edges, int root = 0)
        : n(n_), tin(n_), tout(n_), depth(n_), par(n_, -1), first(n_),
          children(n_), adj(n_) {
        for (auto& e : edges) { adj[e.first].push_back(e.second); adj[e.second].push_back(e.first); }
        dfs(root, -1);
        build_sparse();
    }

    const std::vector<int>& euler_tour() const { return euler; }   // para la animación

    bool is_ancestor(int u, int v) const { return tin[u] <= tin[v] && tin[v] <= tout[u]; }

    int lca(int u, int v) const {                     // O(1)
        int l = first[u], r = first[v];
        if (l > r) std::swap(l, r);
        int j = 31 - __builtin_clz(r - l + 1);
        return better(sp[j][l], sp[j][r - (1 << j) + 1]);
    }

    // Construye el virtual tree de `query` (puede traer duplicados / cualquier orden).
    VTResult build_virtual(std::vector<int> query, VTTrace* tr = nullptr) const {
        VTResult res;
        auto by_tin = [&](int a, int b) { return tin[a] < tin[b]; };
        std::sort(query.begin(), query.end(), by_tin);
        query.erase(std::unique(query.begin(), query.end()), query.end());
        if (tr) tr->sorted_query = query;
        if (query.empty()) return res;                // caso borde: consulta vacía

        std::vector<int> all = query;
        for (size_t i = 0; i + 1 < query.size(); ++i) {
            int l = lca(query[i], query[i + 1]);
            all.push_back(l);
            if (tr) tr->lcas.push_back({query[i], query[i + 1], l});
        }
        std::sort(all.begin(), all.end(), by_tin);
        all.erase(std::unique(all.begin(), all.end()), all.end());
        if (tr) tr->all_nodes = all;

        std::vector<int> st;
        for (int v : all) {
            VTStep step; step.node = v;
            while (!st.empty() && !is_ancestor(st.back(), v)) { step.popped.push_back(st.back()); st.pop_back(); }
            step.parent = st.empty() ? -1 : st.back();
            if (!st.empty()) res.edges.push_back({st.back(), v});
            st.push_back(v);
            step.stack = st;
            if (tr) tr->steps.push_back(step);
        }
        res.nodes = all;
        return res;
    }

    // Variante O(k): exige que `q` esté ordenada por tin y sin duplicados.
    // Una sola pasada: la pila guarda la cadena de ancestros "abierta"; el LCA
    // del tope con el nodo nuevo se inserta en el momento en que se necesita,
    // así que no hace falta una segunda ordenación.
    // Los nodos se devuelven en orden de inserción (no necesariamente por tin).
    VTResult build_virtual_sorted(const std::vector<int>& q) const {
        VTResult res;
        if (q.empty()) return res;
        std::vector<int> st = {q[0]};
        res.nodes.push_back(q[0]);
        for (size_t i = 1; i < q.size(); ++i) {
            int v = q[i], l = lca(st.back(), v);
            if (l != st.back()) {                     // v sale del subárbol del tope
                while (st.size() >= 2 && depth[st[st.size() - 2]] >= depth[l]) {
                    res.edges.push_back({st[st.size() - 2], st.back()});
                    st.pop_back();
                }
                if (st.back() != l) {                 // l es un punto de ramificación nuevo
                    res.edges.push_back({l, st.back()});
                    st.pop_back();
                    st.push_back(l);
                    res.nodes.push_back(l);
                }
            }
            st.push_back(v);
            res.nodes.push_back(v);
        }
        for (size_t i = st.size(); i-- > 1; )         // cerrar la cadena restante
            res.edges.push_back({st[i - 1], st[i]});
        return res;
    }

private:
    std::vector<std::vector<int>> adj;
    std::vector<int> euler;
    std::vector<std::vector<int>> sp;
    int timer = 0;

    int better(int a, int b) const { return depth[a] <= depth[b] ? a : b; }

    // DFS iterativo con pila explícita: mismo orden de visita que la versión
    // recursiva, pero sin riesgo de desbordar la pila del sistema en árboles
    // muy profundos (p.ej. una cadena de 10^6 nodos).
    void dfs(int root, int) {
        euler.reserve(2 * n);
        std::vector<size_t> it(n, 0);                 // siguiente vecino a revisar
        std::vector<int> st = {root};
        par[root] = -1; depth[root] = 0;
        tin[root] = timer++; first[root] = 0; euler.push_back(root);
        while (!st.empty()) {
            int u = st.back();
            if (it[u] < adj[u].size()) {
                int c = adj[u][it[u]++];
                if (c == par[u]) continue;
                par[c] = u; depth[c] = depth[u] + 1;
                children[u].push_back(c);
                tin[c] = timer++;
                first[c] = (int)euler.size(); euler.push_back(c);
                st.push_back(c);
            } else {
                tout[u] = timer - 1;
                st.pop_back();
                if (!st.empty()) euler.push_back(st.back());
            }
        }
    }

    void build_sparse() {
        int m = (int)euler.size(), K = 32 - __builtin_clz(m);
        sp.assign(K, std::vector<int>(m));
        sp[0] = euler;
        for (int j = 1; j < K; ++j)
            for (int i = 0; i + (1 << j) <= m; ++i)
                sp[j][i] = better(sp[j-1][i], sp[j-1][i + (1 << (j-1))]);
    }
};
