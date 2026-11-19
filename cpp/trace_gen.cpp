// trace_gen.cpp - ejecuta el Virtual Tree REAL sobre un árbol de ejemplo y
// escribe la traza (tin/tout, Euler tour, LCAs, pasos de la pila) en JSON. La animación
// de Manim solo lee este archivo: no hay pasos escritos a mano.
// Uso: ./trace_gen > ../manim/trace.json
#include <iostream>
#include "virtual_tree.hpp"
using namespace std;

static void arr(const vector<int>& v) {
    cout << "[";
    for (size_t i = 0; i < v.size(); ++i) cout << (i ? "," : "") << v[i];
    cout << "]";
}

int main() {
    // Árbol de ejemplo (14 nodos, raíz 0)
    vector<pair<int,int>> E = {{0,1},{0,2},{1,3},{1,4},{2,5},{2,6},{3,7},{3,8},
                               {4,9},{5,10},{5,11},{6,12},{12,13}};
    RootedTree t(14, E, 0);

    struct Case { const char* name; vector<int> q; };
    vector<Case> cases = {
        {"Ejemplo general (k = 4)", {10, 7, 13, 9}},       // desordenado a propósito
        {"Caso borde: un solo nodo (k = 1)", {10}},
        {"Caso borde: un nodo es ancestro de otro", {2, 6, 13}},
        {"Tu turno", {12, 8, 11}},                          // ejercicio del video
    };

    cout << "{\n\"tree\":{\"n\":" << t.n << ",\"tin\":"; arr(t.tin);
    cout << ",\"tout\":"; arr(t.tout);
    cout << ",\"depth\":"; arr(t.depth);
    cout << ",\"parent\":"; arr(t.par);
    cout << ",\"euler\":"; arr(t.euler_tour());
    cout << ",\"children\":[";
    for (int u = 0; u < t.n; ++u) { cout << (u ? "," : ""); arr(t.children[u]); }
    cout << "]},\n\"cases\":[\n";
    for (size_t c = 0; c < cases.size(); ++c) {
        VTTrace tr;
        VTResult r = t.build_virtual(cases[c].q, &tr);
        cout << (c ? ",\n" : "") << "{\"name\":\"" << cases[c].name << "\",\"query\":";
        arr(cases[c].q);
        cout << ",\"sorted\":"; arr(tr.sorted_query);
        cout << ",\"lcas\":[";
        for (size_t i = 0; i < tr.lcas.size(); ++i)
            cout << (i ? "," : "") << "{\"a\":" << tr.lcas[i].a << ",\"b\":" << tr.lcas[i].b << ",\"l\":" << tr.lcas[i].l << "}";
        cout << "],\"all\":"; arr(tr.all_nodes);
        cout << ",\"steps\":[";
        for (size_t i = 0; i < tr.steps.size(); ++i) {
            auto& s = tr.steps[i];
            cout << (i ? "," : "") << "{\"node\":" << s.node << ",\"popped\":"; arr(s.popped);
            cout << ",\"parent\":" << s.parent << ",\"stack\":"; arr(s.stack); cout << "}";
        }
        cout << "],\"edges\":[";
        for (size_t i = 0; i < r.edges.size(); ++i)
            cout << (i ? "," : "") << "[" << r.edges[i].first << "," << r.edges[i].second << "]";
        cout << "]}";
    }
    cout << "\n]}\n";
    return 0;
}
