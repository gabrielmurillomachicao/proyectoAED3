"""
virtual_tree_scene.py  -  Video: Virtual Tree (Auxiliary Tree), CS2023 UTEC.

Toda la animación se genera leyendo trace.json, producido por el programa C++
(cpp/trace_gen.cpp) que ejecuta la implementación real de virtual_tree.hpp:
tiempos tin/tout, Euler tour, LCAs, pasos de la pila y aristas resultantes.
El gráfico de costo lee cpp/bench_result.csv (salida de `make bench`).
Esta escena solo dibuja; no calcula ni escribe a mano ningún paso del algoritmo.

    manim -qh virtual_tree_scene.py VirtualTreeVideo

Video sin voz: cada subtítulo permanece en pantalla al menos el tiempo que toma
leerlo (READ_CPS caracteres por segundo). Duración objetivo: menos de 5 minutos.

Guion:
  1. El problema y una pregunta concreta     6. Ejemplo completo (3 pasos)
  2. ¿Qué es? (TDA)                          7. ¿Por qué bastan los pares vecinos?
  3. Herramienta 1: tin/tout (+ pregunta)    8. Caso borde
  4. Herramienta 2: LCA                      9. Tu turno (ejercicio)
  5. El algoritmo en 3 pasos                10. Costo medido · resumen · créditos
"""
import csv
import json
import os
from manim import *

# ---- Integrantes del grupo (aparecen al inicio y en los créditos) ----
MEMBERS = ["Gabriel Murillo Machicao", "Juan Pablo Saavedra Ruiz"]
HERE = os.path.dirname(os.path.abspath(__file__))
TRACE = os.path.join(HERE, "trace.json")
BENCH = os.path.join(HERE, "..", "cpp", "bench_result.csv")

C_BASE, C_QUERY, C_LCA, C_EDGE = "#4A4A4A", "#F39C12", "#2ECC71", "#F1C40F"
C_PATH, C_BAD, C_SEEN = "#5DADE2", "#E74C3C", "#2E5E7E"
C_SUB1, C_SUB2 = "#3F6FB5", "#9B59B6"     # colores para dos subárboles
R = 0.27              # radio de los nodos
PANEL_X = 4.55        # centro del panel lateral derecho
TREE_ORIGIN = (-2.2, 2.3)
READ_CPS = 15.0       # velocidad de lectura supuesta (caracteres por segundo)

STEP_NAMES = ["1 · Ordenar por tin", "2 · Añadir LCA", "3 · Pila"]


def read_time(text):
    """Tiempo mínimo para leer un texto en pantalla, sin voz."""
    return max(1.8, 0.6 + len(text) / READ_CPS)


def layout(children, root, x_scale, y_gap, origin):
    """Posiciones tipo 'tidy tree': hojas equiespaciadas, padre centrado."""
    pos, counter = {}, [0]

    def rec(u, d):
        kids = children.get(u, [])
        if not kids:
            x = counter[0]; counter[0] += 1
        else:
            xs = [rec(c, d + 1) for c in kids]
            x = sum(xs) / len(xs)
        pos[u] = (x, d)
        return x

    rec(root, 0)
    cx = (max(p[0] for p in pos.values()) + min(p[0] for p in pos.values())) / 2
    return {u: np.array([origin[0] + (x - cx) * x_scale, origin[1] - d * y_gap, 0])
            for u, (x, d) in pos.items()}


def fit(group, max_w=12.4):
    """Escala el grupo si excede el ancho visible y lo centra horizontalmente."""
    if group.width > max_w:
        group.scale_to_fit_width(max_w)
    return group.set_x(0)


def inside(m, margin=0.45):
    """Desplaza el objeto para que no toque los bordes del cuadro (14.2 x 8)."""
    xr, xl = 7.1 - margin, -7.1 + margin
    if m.get_right()[0] > xr:
        m.shift(LEFT * (m.get_right()[0] - xr))
    if m.get_left()[0] < xl:
        m.shift(RIGHT * (xl - m.get_left()[0]))
    return m


def chip(v, color, size=0.46, fs=20):
    sq = Square(size, color=color, fill_opacity=0.25, stroke_width=2)
    return VGroup(sq, Text(str(v), font_size=fs).move_to(sq))


def chips(values, color, size=0.46):
    return VGroup(*[chip(v, color, size) for v in values]).arrange(RIGHT, buff=0.08)


def load_bench():
    """Lee la fila n = 10^6 del experimento 1 de bench_result.csv."""
    try:
        with open(BENCH, encoding="utf-8") as f:
            rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
        for r in rows:
            if r[0] == "1000000" and len(r) == 3:
                return float(r[1]), float(r[2])
    except (OSError, ValueError):
        pass
    return None


class VirtualTreeVideo(Scene):
    # ------------------------------------------------------------------
    def construct(self):
        with open(TRACE, encoding="utf-8") as f:
            self.data = json.load(f)
        tr = self.data["tree"]
        self.n = tr["n"]
        self.tin, self.tout = tr["tin"], tr["tout"]
        self.par, self.depth = tr["parent"], tr["depth"]
        self.children = {u: tr["children"][u] for u in range(self.n)}
        self.cases = self.data["cases"]

        self.speed = 1.0
        self.caption = None
        self.cap_t0, self.cap_need = 0.0, 0.0
        self.cap_log = []
        self.steps_ui = None

        self.title_card()
        self.motivation()
        self.concept()
        self.dfs_times()
        self.lca_intro()
        self.roadmap()
        self.run_case(self.cases[0], full=True)
        self.why_adjacent()
        self.speed = 0.8
        self.run_case(self.cases[2], full=False)
        self.speed = 1.0
        self.quiz(self.cases[3])
        self.cost()
        self.summary()
        self.credits()

        self.cap_log.append({"t": self.renderer.time, "text": "<fin>"})
        log = os.environ.get("VT_CAPTION_LOG")
        if log:
            with open(log, "w", encoding="utf-8") as f:
                json.dump(self.cap_log, f, ensure_ascii=False, indent=0)

    # ---------------- utilidades ----------------
    def P(self, *anims, rt=0.6):
        self.play(*anims, run_time=rt * self.speed)

    def W(self, t):
        self.wait(t * self.speed)

    def flush_caption(self):
        """Espera lo que falte para que el subtítulo actual se haya podido leer."""
        if self.caption is not None:
            rem = self.cap_need - (self.renderer.time - self.cap_t0)
            if rem > 0.05:
                self.wait(rem)

    def set_caption(self, text, color=WHITE, size=24):
        self.flush_caption()
        new = Text(text, font_size=size, color=color)
        fit(new, 13.4).to_edge(DOWN, buff=0.32)
        if self.caption is None:
            self.play(FadeIn(new), run_time=0.3)
        else:
            self.play(ReplacementTransform(self.caption, new), run_time=0.3)
        self.caption = new
        self.cap_t0, self.cap_need = self.renderer.time, read_time(text)
        self.cap_log.append({"t": self.cap_t0, "text": text, "need": self.cap_need})

    def clear_caption(self):
        if self.caption is not None:
            self.flush_caption()
            self.play(FadeOut(self.caption), run_time=0.3)
            self.cap_log.append({"t": self.renderer.time, "text": "<off>"})
            self.caption = None

    def show_slide(self, title, items, end=1.0):
        """items: lista de (texto, color). Cada línea queda el tiempo de leerla."""
        h = Text(title, font_size=36, weight=BOLD).to_edge(UP)
        body = VGroup(*[Text(t, font_size=27, color=c) for t, c in items])
        body.arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        fit(body).next_to(h, DOWN, buff=0.75)
        self.play(Write(h), run_time=0.8)
        for (t, _), l in zip(items, body):
            self.play(FadeIn(l, shift=RIGHT * 0.3), run_time=0.5)
            self.wait(max(0.8, len(t) / READ_CPS))
        self.wait(end)
        self.play(FadeOut(h), FadeOut(body))

    def build_tree(self):
        """Árbol original con etiquetas t=tin. nodes[u] = VGroup(círculo, número, tin)."""
        pos = layout(self.children, 0, 0.95, 0.95, TREE_ORIGIN)
        edges, nodes = {}, {}
        for u in range(self.n):
            for c in self.children[u]:
                edges[c] = Line(pos[u], pos[c], color=GRAY, stroke_width=2)
        for u in range(self.n):
            circ = Circle(R, color=WHITE, fill_color=C_BASE, fill_opacity=1, stroke_width=2).move_to(pos[u])
            lab = Text(str(u), font_size=20).move_to(pos[u])
            tin = Text(f"t={self.tin[u]}", font_size=16, color=GRAY_B).next_to(circ, UR, buff=-0.06)
            circ.set_z_index(2); lab.set_z_index(3)
            nodes[u] = VGroup(circ, lab, tin)
        return pos, edges, nodes

    def bare(self, nodes, us=None):
        """Círculo + número (sin la etiqueta tin)."""
        us = range(self.n) if us is None else us
        return VGroup(*[VGroup(nodes[u][0], nodes[u][1]) for u in us])

    def path_lines(self, pos, u, top, color, width=6):
        """Líneas resaltadas del camino real u -> top (top ancestro de u)."""
        lines = []
        while u != top:
            p = self.par[u]
            lines.append(Line(pos[p], pos[u], color=color, stroke_width=width).set_z_index(1))
            u = p
        return lines[::-1]

    def path_str(self, p, c):
        nodes = [c]
        while nodes[-1] != p:
            nodes.append(self.par[nodes[-1]])
        return " → ".join(str(x) for x in nodes[::-1])

    def subtree(self, u):
        return [v for v in range(self.n) if self.tin[u] <= self.tin[v] <= self.tout[u]]

    def virtual_layout(self, case, scale=1.6, gap=1.3, origin=(0, 1.4)):
        vch = {u: [] for u in case["all"]}
        has_parent = set()
        for p, c in case["edges"]:
            vch[p].append(c); has_parent.add(c)
        root = [u for u in case["all"] if u not in has_parent][0]
        return layout(vch, root, scale, gap, origin)

    def countdown(self, secs, where):
        timer = None
        for s in range(secs, 0, -1):
            t = Text(str(s), font_size=36, color=C_EDGE).move_to(where)
            grp = VGroup(Circle(0.42, color=C_EDGE).move_to(t), t)
            if timer is None:
                self.play(FadeIn(grp), run_time=0.25)
            else:
                self.play(ReplacementTransform(timer, grp), run_time=0.25)
            timer = grp
            self.wait(0.75)
        self.play(FadeOut(timer), run_time=0.25)

    # columna izquierda: paso actual + leyenda de colores
    def show_steps(self):
        items = VGroup(*[Text(t, font_size=18, color=GRAY_D) for t in STEP_NAMES])
        items.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        leg = VGroup(
            VGroup(Dot(radius=0.1, color=C_QUERY), Text("consulta", font_size=17)).arrange(RIGHT, buff=0.12),
            VGroup(Dot(radius=0.1, color=C_LCA), Text("LCA añadido", font_size=17)).arrange(RIGHT, buff=0.12),
            VGroup(Line(ORIGIN, RIGHT * 0.3, color=C_EDGE, stroke_width=5), Text("arista virtual", font_size=17)).arrange(RIGHT, buff=0.12),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        col = VGroup(items, leg).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        col.to_corner(UL, buff=0.35).shift(DOWN * 0.7)
        self.steps_ui = items
        self.legend_ui = leg
        self.P(FadeIn(col), rt=0.4)

    def set_step(self, i):
        self.P(*[it.animate.set_color(C_EDGE if j == i else GRAY_D) for j, it in enumerate(self.steps_ui)], rt=0.3)

    # ---------------- 1. título ----------------
    def title_card(self):
        t = Text("Virtual Tree (Auxiliary Tree)", font_size=48, weight=BOLD)
        s = Text("CS2023 · Algoritmos y Estructuras de Datos · Proyecto Final 2", font_size=22, color=GRAY_B)
        m = Text("   ·   ".join(MEMBERS), font_size=26).set_color(BLUE_B)
        VGroup(t, s, m).arrange(DOWN, buff=0.45)
        self.play(Write(t), run_time=1.2); self.play(FadeIn(s), FadeIn(m))
        self.wait(1.8)
        self.play(FadeOut(VGroup(t, s, m)))

    # ---------------- 2. motivación ----------------
    def motivation(self):
        case = self.cases[0]
        h = Text("El problema", font_size=32, weight=BOLD).to_edge(UP, buff=0.3)
        pos, edges, nodes = self.build_tree()
        base = VGroup(*edges.values(), self.bare(nodes))
        self.play(Write(h), FadeIn(base))
        self.set_caption("Un árbol enorme: imagina n = 1 000 000 de nodos")
        q = sorted(set(case["query"]))
        self.play(*[nodes[u][0].animate.set_fill(C_QUERY) for u in q])
        self.set_caption(f"Cada consulta marca solo unos pocos nodos: aquí k = {len(q)}", C_QUERY)
        question = VGroup(
            Text("Pregunta de ejemplo:", font_size=20, color=GRAY_B),
            Text("¿cuántas aristas tiene el menor", font_size=21),
            Text("subárbol que une los nodos", font_size=21),
            Text("marcados?", font_size=21),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([PANEL_X, 2.0, 0])
        qframe = SurroundingRectangle(question, color=C_QUERY, buff=0.2, corner_radius=0.1)
        inside(VGroup(question, qframe))
        self.play(FadeIn(question), Create(qframe))
        self.set_caption("Recorrer todo el árbol en cada consulta cuesta O(n): muy lento")
        order = sorted(range(self.n), key=lambda u: self.tin[u])
        self.play(LaggedStart(*[Indicate(nodes[u][0], color=C_PATH, scale_factor=1.2) for u in order],
                              lag_ratio=0.15), run_time=2.2)
        lcas = [u for u in case["all"] if u not in q]
        self.set_caption("Idea: quedarnos con ellos y los puntos donde sus caminos se separan", C_LCA)
        self.play(*[nodes[u][0].animate.set_fill(C_LCA) for u in lcas])
        keep = set(case["all"])
        vpos = self.virtual_layout(case, origin=(-1.4, 1.2))
        self.flush_caption()
        self.play(*[FadeOut(self.bare(nodes, [u])) for u in range(self.n) if u not in keep],
                  *[FadeOut(e) for e in edges.values()], run_time=0.9)
        self.play(*[self.bare(nodes, [u]).animate.move_to(vpos[u]) for u in keep], run_time=1.1)
        vlines = [Line(vpos[p], vpos[c], color=C_EDGE, stroke_width=5).set_z_index(0) for p, c in case["edges"]]
        self.play(*[Create(l) for l in vlines], run_time=0.7)
        self.set_caption(f"Eso es el Virtual Tree: {len(keep)} nodos en vez de {self.n}. Con él responderemos la pregunta", C_EDGE)
        self.clear_caption()
        self.play(FadeOut(VGroup(h, question, qframe, *vlines, self.bare(nodes, keep))))

    # ---------------- 3. TDA ----------------
    def concept(self):
        self.show_slide("¿Qué es un Virtual Tree? (TDA)", [
            ("Entrada: un árbol fijo y k nodos de consulta.", WHITE),
            ("Salida: esos k nodos + los LCA necesarios.", WHITE),
            ("Tamaño: a lo sumo 2k − 1 nodos, sin importar n.", C_EDGE),
        ], end=0.5)

    # ---------------- 4. tin / tout ----------------
    def dfs_times(self):
        h = Text("Herramienta 1: tiempos del DFS (tin y tout)", font_size=30, weight=BOLD).to_edge(UP, buff=0.3)
        pos, edges, nodes = self.build_tree()
        base = VGroup(*edges.values(), self.bare(nodes))
        self.play(Write(h), FadeIn(base))

        order = sorted(range(self.n), key=lambda u: self.tin[u])
        cells = VGroup(*[chip(u, C_PATH, 0.42, 17) for u in order]).arrange(RIGHT, buff=0.04)
        cells.move_to([0.6, -2.55, 0])
        idx = VGroup(*[Text(str(i), font_size=14, color=GRAY_B).next_to(cells[i], DOWN, buff=0.07)
                       for i in range(self.n)])
        idx_lbl = Text("tin →", font_size=15, color=GRAY_B).next_to(idx, LEFT, buff=0.2)
        arr_lbl = Text("nodo →", font_size=15, color=GRAY_B).next_to(cells, LEFT, buff=0.2)

        self.set_caption("El DFS numera cada nodo al ENTRAR: eso es tin")
        dot = Dot(pos[0], color=C_EDGE, radius=0.11).set_z_index(5)
        self.play(FadeIn(dot), FadeIn(idx), FadeIn(idx_lbl), FadeIn(arr_lbl))
        seen = set()
        for i, u in enumerate(self.data["tree"]["euler"]):
            anims = [dot.animate.move_to(pos[u])] if i > 0 else []
            first = u not in seen
            if first:
                seen.add(u)
                anims += [FadeIn(nodes[u][2]), nodes[u][0].animate.set_fill(C_SEEN),
                          FadeIn(cells[self.tin[u]], shift=DOWN * 0.2)]
            self.play(*anims, run_time=0.3 if first else 0.16)
        self.play(FadeOut(dot), *[nodes[u][0].animate.set_fill(C_BASE) for u in range(self.n)], run_time=0.5)

        u = 2
        box = SurroundingRectangle(VGroup(*cells[self.tin[u]:self.tout[u] + 1]), color=C_LCA, buff=0.05)
        self.set_caption(f"tout = último tin de su subárbol. Subárbol de {u}: de {self.tin[u]} a {self.tout[u]}", C_LCA)
        self.play(*[nodes[v][0].animate.set_fill(C_LCA) for v in self.subtree(u)], Create(box))

        f1 = Text("u es ancestro de v", font_size=22)
        f2 = Text("⇔  tin[u] ≤ tin[v] ≤ tout[u]", font_size=22, color=C_EDGE)
        formula = VGroup(f1, f2).arrange(DOWN, buff=0.15).move_to([PANEL_X - 0.3, 2.2, 0])
        frame = SurroundingRectangle(formula, color=C_EDGE, buff=0.2, corner_radius=0.1)
        self.set_caption("Cada subárbol es un bloque contiguo. Por eso:")
        self.play(FadeIn(formula), Create(frame))

        v = 10
        ex1 = Text(f"¿{u} es ancestro de {v}?  {self.tin[v]} ∈ [{self.tin[u]}, {self.tout[u]}]  sí",
                   font_size=20, color=C_LCA).next_to(frame, DOWN, buff=0.45)
        self.set_caption(f"tin({v}) = {self.tin[v]} cae en [{self.tin[u]}, {self.tout[u]}]: {u} es ancestro de {v}", C_LCA)
        inside(ex1)
        self.play(Indicate(nodes[v][0], color=C_QUERY), Indicate(cells[self.tin[v]], color=C_QUERY), FadeIn(ex1))

        w = 1
        self.set_caption(f"Pregunta rápida: ¿{w} es ancestro de {v}?", C_EDGE)
        qmark = Text(f"¿{w} es ancestro de {v}?", font_size=20, color=C_EDGE).next_to(ex1, DOWN, buff=0.3)
        self.play(FadeIn(qmark))
        self.flush_caption()
        self.countdown(3, [PANEL_X - 0.3, -0.7, 0])
        ex2 = Text(f"¿{w} es ancestro de {v}?  {self.tin[v]} ∉ [{self.tin[w]}, {self.tout[w]}]  no",
                   font_size=20, color=C_BAD).move_to(qmark)
        box2 = SurroundingRectangle(VGroup(*cells[self.tin[w]:self.tout[w] + 1]), color=C_BAD, buff=0.05)
        self.play(ReplacementTransform(qmark, ex2), Create(box2),
                  *[nodes[x][0].animate.set_fill(C_BAD) for x in self.subtree(w)])
        self.set_caption(f"No: {self.tin[v]} ∉ [{self.tin[w]}, {self.tout[w]}]. Y la prueba cuesta O(1)", C_BAD)
        self.clear_caption()
        self.play(FadeOut(VGroup(h, base, *[nodes[x][2] for x in range(self.n)], cells, idx, idx_lbl,
                                 arr_lbl, box, box2, formula, frame, ex1, ex2)))

    # ---------------- 5. LCA ----------------
    def lca_intro(self):
        h = Text("Herramienta 2: ancestro común más bajo (LCA)", font_size=30, weight=BOLD).to_edge(UP, buff=0.3)
        pos, edges, nodes = self.build_tree()
        tree = VGroup(*edges.values(), *nodes.values())
        self.play(Write(h), FadeIn(tree))
        a, b, l = 9, 10, 0
        self.set_caption(f"lca({a}, {b}): subimos desde ambos hasta que los caminos se juntan")
        self.play(nodes[a][0].animate.set_fill(C_QUERY), nodes[b][0].animate.set_fill(C_QUERY), run_time=0.5)
        pl = self.path_lines(pos, a, l, C_PATH) + self.path_lines(pos, b, l, C_PATH)
        self.play(*[Create(x) for x in pl], run_time=1.4)
        self.play(nodes[l][0].animate.set_fill(C_LCA), Flash(nodes[l][0], color=C_LCA), run_time=0.6)
        self.set_caption(f"lca({a}, {b}) = {l}: el ancestro común más profundo", C_LCA)
        note = VGroup(
            Text("Euler tour + Sparse Table:", font_size=20),
            Text("se precalcula en O(n log n)", font_size=20, color=C_EDGE),
            Text("y cada LCA cuesta O(1)", font_size=20, color=C_EDGE),
        ).arrange(DOWN, buff=0.15).move_to([PANEL_X, 1.6, 0])
        self.set_caption("Con un preproceso, cada LCA cuesta O(1)")
        self.play(FadeIn(note))
        self.clear_caption()
        self.play(FadeOut(VGroup(h, tree, note, *pl)))

    # ---------------- 6. hoja de ruta ----------------
    def roadmap(self):
        self.show_slide("El algoritmo en 3 pasos", [
            ("1.  Ordenar la consulta por tin.", WHITE),
            ("2.  Añadir el LCA de cada par vecino.", C_LCA),
            ("3.  Pila: el tope es el padre virtual.", C_EDGE),
        ], end=0.5)

    # ---------------- 7 y 9. ejemplo y caso borde ----------------
    def run_case(self, case, full):
        n = self.n
        pos, edges, nodes = self.build_tree()
        header = Text(case["name"], font_size=28, weight=BOLD).to_edge(UP, buff=0.3)
        tree_group = VGroup(*edges.values(), *nodes.values())
        self.P(Write(header), FadeIn(tree_group), rt=0.9)
        self.show_steps()

        q = case["query"]
        k = len(set(q))
        if full:
            self.set_caption(f"Consulta: {q}, en cualquier orden (k = {k})", C_QUERY)
        else:
            self.set_caption(f"Caso borde {q}: 2 es ancestro de 6, y 6 de 13", C_QUERY)
        self.P(*[nodes[u][0].animate.set_fill(C_QUERY) for u in set(q)])

        # ---- paso 1
        self.set_step(0)
        row_lbl = Text("orden por tin", font_size=18, color=GRAY_B).move_to([PANEL_X, 2.75, 0])
        row = chips(case["sorted"], C_QUERY).next_to(row_lbl, DOWN, buff=0.15)
        if full:
            self.set_caption("Paso 1: ordenar por tin  (" + ",  ".join(f"{v}→{self.tin[v]}" for v in case["sorted"]) + ")")
            src = chips(q, C_QUERY).next_to(row_lbl, DOWN, buff=0.15)
            self.P(FadeIn(row_lbl), FadeIn(src))
            dest = {v: i for i, v in enumerate(case["sorted"])}
            self.P(*[src[i].animate.move_to(row[dest[v]]) for i, v in enumerate(q) if v in dest], rt=1.0)
            self.remove(src); self.add(row)
        else:
            self.P(FadeIn(row_lbl), FadeIn(row, shift=LEFT * 0.3))

        # ---- paso 2
        self.set_step(1)
        lca_rows = VGroup()
        if full:
            self.set_caption(f"Paso 2: LCA de cada par vecino (solo k − 1 = {k - 1} pares)")
        else:
            self.set_caption("Sus LCA (2 y 6) ya están en la consulta: no se agrega nada")
        lca_lbl = Text("LCA de pares vecinos", font_size=18, color=GRAY_B).next_to(row, DOWN, buff=0.45)
        self.P(FadeIn(lca_lbl), rt=0.3)
        lca_rows.add(lca_lbl)
        for i, item in enumerate(case["lcas"]):
            a, b, l = item["a"], item["b"], item["l"]
            new = l not in case["sorted"]
            pair = SurroundingRectangle(VGroup(row[i], row[i + 1]), color=WHITE, buff=0.04)
            line = Text(f"lca({a}, {b}) = {l}", font_size=20, color=C_LCA if new else GRAY_A)
            line.next_to(lca_rows, DOWN, buff=0.15)
            lca_rows.add(line)
            txt = f"lca({a}, {b}) = {l}" + ("  →  nodo nuevo" if new else "  →  ya estaba")
            pl = self.path_lines(pos, a, l, C_PATH) + self.path_lines(pos, b, l, C_PATH)
            if full:
                self.set_caption(txt, C_LCA if new else WHITE)
            anims = [Create(pair), *[Create(x) for x in pl], FadeIn(line, shift=LEFT * 0.2)]
            if new:
                anims.append(nodes[l][0].animate.set_fill(C_LCA))
            self.P(*anims, rt=1.0)
            self.flush_caption()
            self.P(FadeOut(VGroup(*pl)), FadeOut(pair), rt=0.3)

        # ---- paso 3
        self.set_step(2)
        all_set = set(case["all"])
        dim = [nodes[u].animate.set_opacity(0.18) for u in range(n) if u not in all_set]
        dim += [e.animate.set_opacity(0.12) for e in edges.values()]
        all_lbl = Text("consulta + LCA, por tin", font_size=18, color=GRAY_B).move_to(row_lbl)
        all_row = VGroup(*[chip(u, C_QUERY if u in q else C_LCA) for u in case["all"]])
        all_row.arrange(RIGHT, buff=0.08).next_to(all_lbl, DOWN, buff=0.15)
        if full:
            self.set_caption("Paso 3: recorrer todo por tin con una pila")
        self.P(*dim, FadeOut(lca_rows), ReplacementTransform(row_lbl, all_lbl),
               ReplacementTransform(row, all_row), rt=0.8)
        row_lbl, row = all_lbl, all_row
        stack_title = Text("pila (tope ↑)", font_size=18, color=GRAY_B).move_to(np.array([PANEL_X, -1.75, 0]))
        self.P(FadeIn(stack_title), rt=0.3)
        if full:
            self.set_caption("Regla: sacar los NO ancestros; el tope que queda es el padre", C_EDGE)
        else:
            self.set_caption("La pila nunca saca nada: cada nodo cuelga del anterior")

        boxes, rings, vedges, pointer = [], [], [], None
        explained_compress = explained_rings = explained_pop = False

        def box_for(v, i):
            sq = Square(0.5, color=C_EDGE, fill_opacity=0.25, stroke_width=2)
            sq.move_to(np.array([PANEL_X, -1.2 + i * 0.55, 0]))
            return VGroup(sq, Text(str(v), font_size=20).move_to(sq))

        def ring_for(v):
            return Circle(R + 0.09, color=C_EDGE, stroke_width=4).move_to(pos[v]).set_z_index(4)

        for idx, st in enumerate(case["steps"]):
            v, p = st["node"], st["parent"]
            new_ptr = SurroundingRectangle(row[idx], color=WHITE, buff=0.05, stroke_width=3)
            ptr_anim = Create(new_ptr) if pointer is None else pointer.animate.move_to(new_ptr)
            if pointer is None:
                pointer = new_ptr
            self.P(ptr_anim, Indicate(nodes[v][0], color=C_PATH, scale_factor=1.25), rt=0.5)

            if full:
                popped = st["popped"]
                if p >= 0:
                    why = f"padre = {p}  ({self.tin[v]} ∈ [{self.tin[p]}, {self.tout[p]}])"
                else:
                    why = "pila vacía → es la raíz"
                if popped:
                    outs = " y ".join(map(str, popped))
                    self.set_caption(f"{v}: sacar {outs} (no son ancestros);  {why}" if len(popped) > 1 else
                                     f"{v}: sacar {outs} ({self.tin[v]} ∉ [{self.tin[popped[0]]}, {self.tout[popped[0]]}]);  {why}",
                                     C_BAD)
                else:
                    self.set_caption(f"{v}: {why}", C_EDGE if p >= 0 else C_LCA)
                for u in popped:
                    top, rg = boxes.pop(), rings.pop()
                    self.P(top.animate.set_color(C_BAD), rg.animate.set_color(C_BAD), rt=0.3)
                    self.P(FadeOut(top, shift=RIGHT * 0.6), FadeOut(rg), rt=0.35)
                if popped and not explained_pop:
                    explained_pop = True
                    self.set_caption("Sacarlo es seguro: lo que viene (mayor tin) tampoco está en su subárbol", C_BAD)
                if p >= 0:
                    ve = Line(pos[p], pos[v], color=C_EDGE, stroke_width=6).set_z_index(1)
                    vedges.append(ve)
                    real = self.path_lines(pos, v, p, WHITE, width=3)
                    anims = [Create(ve)]
                    if len(real) > 1:
                        anims += [ShowPassingFlash(x.copy().set_stroke(width=8), time_width=0.6) for x in real]
                    self.P(*anims, rt=0.8)
                    if len(real) > 1 and not explained_compress:
                        explained_compress = True
                        self.set_caption(f"La arista ({p}, {v}) resume el camino {self.path_str(p, v)}", C_PATH)
                nb, rg = box_for(v, len(boxes)), ring_for(v)
                self.P(FadeIn(nb, shift=DOWN * 0.4), Create(rg), rt=0.4)
                boxes.append(nb); rings.append(rg)
                if len(boxes) == 3 and not explained_rings:
                    explained_rings = True
                    self.set_caption("Anillos dorados = la pila: un camino desde la raíz", C_EDGE)
            else:
                anims = []
                for u in st["popped"]:
                    anims += [FadeOut(boxes.pop(), shift=RIGHT * 0.6), FadeOut(rings.pop())]
                if p >= 0:
                    ve = Line(pos[p], pos[v], color=C_EDGE, stroke_width=6).set_z_index(1)
                    vedges.append(ve)
                    anims.append(Create(ve))
                nb, rg = box_for(v, len(boxes)), ring_for(v)
                boxes.append(nb); rings.append(rg)
                anims += [FadeIn(nb, shift=DOWN * 0.4), Create(rg)]
                self.P(*anims, rt=0.7)
                self.W(0.4)

        # ---- resultado
        self.clear_caption()
        self.P(FadeOut(tree_group), FadeOut(VGroup(*vedges, *boxes, *rings)), FadeOut(stack_title),
               FadeOut(row_lbl), FadeOut(row), FadeOut(pointer), FadeOut(self.steps_ui), rt=0.7)
        vpos = self.virtual_layout(case)
        vnodes = {}
        for u in case["all"]:
            col = C_QUERY if u in q else C_LCA
            circ = Circle(R * 1.3, color=WHITE, fill_color=col, fill_opacity=1, stroke_width=2).move_to(vpos[u])
            vnodes[u] = VGroup(circ, Text(str(u), font_size=24).move_to(vpos[u])).set_z_index(2)
        vlines = {(p, c): Line(vpos[p], vpos[c], color=C_EDGE, stroke_width=5) for p, c in case["edges"]}
        self.P(*[Create(ln) for ln in vlines.values()], *[FadeIn(g) for g in vnodes.values()], rt=0.9)
        res = Text(f"{len(case['all'])} nodos y {len(case['edges'])} aristas  (cota: 2k − 1 = {2*k-1})",
                   font_size=26, color=C_EDGE).to_edge(DOWN, buff=1.05)
        self.P(FadeIn(res), rt=0.4)

        extra = VGroup()
        if full:
            # aplicación: longitud de cada arista virtual = diferencia de profundidades
            lens = []
            for (p, c), ln in vlines.items():
                d = self.depth[c] - self.depth[p]
                lens.append(d)
                side = LEFT if vpos[c][0] < vpos[p][0] else RIGHT
                extra.add(Text(str(d), font_size=28, weight=BOLD, color=C_PATH).next_to(ln.get_center(), side, buff=0.14))
            self.set_caption("Cada arista mide lo que su camino: (2, 13) vale 3", C_PATH)
            self.P(FadeIn(extra), rt=0.6)
            ans = VGroup(Text("Pregunta inicial:", font_size=21, color=GRAY_B),
                         Text(" + ".join(map(str, lens)), font_size=25, color=C_QUERY),
                         Text(f"= {sum(lens)} aristas", font_size=27, weight=BOLD, color=C_QUERY)).arrange(DOWN, buff=0.15)
            inside(ans.move_to([PANEL_X, 0.6, 0]))
            self.set_caption(f"Respuesta: {sum(lens)} aristas, calculada con solo {len(case['all'])} nodos", C_QUERY)
            self.P(FadeIn(ans), rt=0.5)
            extra.add(ans)
        else:
            self.set_caption("(6, 13) salta el 12. Con k = 1, sería un solo nodo")
        self.clear_caption()
        self.P(FadeOut(VGroup(res, header, extra, self.legend_ui, *vlines.values(), *vnodes.values())), rt=0.6)

    # ---------------- 8. por qué bastan los pares vecinos ----------------
    def why_adjacent(self):
        case = self.cases[0]
        h = Text("¿Por qué bastan los pares vecinos?", font_size=30, weight=BOLD).to_edge(UP, buff=0.3)
        pos, edges, nodes = self.build_tree()
        tree = VGroup(*edges.values(), self.bare(nodes))
        self.play(Write(h), FadeIn(tree))
        s1, s2 = self.subtree(1), self.subtree(2)
        sq = case["sorted"]
        self.set_caption("Subárbol de 1 en azul, de 2 en morado")
        self.play(*[nodes[u][0].animate.set_fill(C_SUB1) for u in s1],
                  *[nodes[u][0].animate.set_fill(C_SUB2) for u in s2])
        rings = [Circle(R + 0.09, color=C_QUERY, stroke_width=5).move_to(pos[u]).set_z_index(4) for u in sq]
        lbl = Text("consulta por tin", font_size=18, color=GRAY_B).move_to([PANEL_X, 2.6, 0])
        row = VGroup(*[chip(u, C_SUB1 if u in s1 else C_SUB2, 0.6, 24) for u in sq]).arrange(RIGHT, buff=0.12)
        row.next_to(lbl, DOWN, buff=0.2)
        self.play(*[Create(r) for r in rings], FadeIn(lbl), FadeIn(row))

        a, b = sq[0], sq[-1]
        pl = self.path_lines(pos, a, 0, WHITE) + self.path_lines(pos, b, 0, WHITE)
        self.set_caption(f"{a} y {b} no son vecinos y su LCA es 0. ¿Lo encontramos?")
        self.play(*[Create(x) for x in pl], Flash(nodes[0][0], color=WHITE), run_time=1.2)

        i = next(j for j in range(len(sq) - 1) if (sq[j] in s1) != (sq[j + 1] in s1))
        cut = DashedLine(row[i].get_corner(UR) + RIGHT * 0.06 + UP * 0.15,
                         row[i + 1].get_corner(DL) + LEFT * 0.06 + DOWN * 0.15, color=C_BAD, stroke_width=4)
        self.set_caption(f"En el orden, el color cambia una vez: entre {sq[i]} y {sq[i + 1]}", C_BAD)
        self.play(Create(cut))
        l = next(x["l"] for x in case["lcas"] if x["a"] == sq[i])
        got = Text(f"lca({sq[i]}, {sq[i + 1]}) = {l}  (ya calculado)", font_size=22, color=C_LCA).next_to(row, DOWN, buff=0.45)
        inside(got)
        self.set_caption(f"Y ese par vecino ya dio lca({sq[i]}, {sq[i + 1]}) = {l}", C_LCA)
        self.play(FadeIn(got))
        bound = Text("k + (k − 1) = 2k − 1 nodos", font_size=24, color=C_EDGE).next_to(got, DOWN, buff=0.5)
        inside(bound)
        self.set_caption("Por eso bastan k − 1 LCA: a lo sumo 2k − 1 nodos", C_EDGE)
        self.play(FadeIn(bound))
        self.clear_caption()
        self.play(FadeOut(VGroup(h, tree, *rings, *pl, lbl, row, cut, got, bound)))

    # ---------------- 10. ejercicio ----------------
    def quiz(self, case):
        h = Text("Tu turno", font_size=32, weight=BOLD).to_edge(UP, buff=0.3)
        pos, edges, nodes = self.build_tree()
        tree = VGroup(*edges.values(), *nodes.values())
        self.play(Write(h), FadeIn(tree))
        q = case["query"]
        self.play(*[nodes[u][0].animate.set_fill(C_QUERY) for u in q])
        self.set_caption(f"Consulta {q}: ¿cuál es su virtual tree?", C_QUERY)
        pause = Text("Pausa el video y resuélvelo", font_size=22, weight=BOLD).move_to([PANEL_X - 0.25, 2.4, 0])
        hint = VGroup(
            Text("Pista:", font_size=19, color=GRAY_B),
            Text("1) ordena por tin", font_size=19),
            Text("2) LCA de pares vecinos", font_size=19),
            Text("3) pila", font_size=19),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(pause, DOWN, buff=0.45)
        self.play(FadeIn(pause), FadeIn(hint))
        self.flush_caption()
        self.countdown(4, [PANEL_X - 0.25, -1.4, 0])
        self.play(FadeOut(pause), FadeOut(hint))

        lbl = Text("orden por tin", font_size=18, color=GRAY_B).move_to([PANEL_X, 2.75, 0])
        row = chips(case["sorted"], C_QUERY).next_to(lbl, DOWN, buff=0.15)
        lines, prev = VGroup(), row
        lca_txt = ", ".join(f"lca({x['a']}, {x['b']}) = {x['l']}" for x in case["lcas"])
        self.set_caption(f"Solución: {lca_txt}", C_LCA)
        self.play(FadeIn(lbl), FadeIn(row))
        for item in case["lcas"]:
            ln = Text(f"lca({item['a']}, {item['b']}) = {item['l']}", font_size=20, color=C_LCA).next_to(prev, DOWN, buff=0.2)
            lines.add(ln); prev = ln
            self.play(FadeIn(ln, shift=LEFT * 0.2), nodes[item["l"]][0].animate.set_fill(C_LCA), run_time=0.5)
        all_set = set(case["all"])
        vls = [Line(pos[p], pos[c], color=C_EDGE, stroke_width=6).set_z_index(1) for p, c in case["edges"]]
        self.play(*[nodes[u].animate.set_opacity(0.18) for u in range(self.n) if u not in all_set],
                  *[e.animate.set_opacity(0.12) for e in edges.values()], run_time=0.5)
        self.play(*[Create(l) for l in vls], run_time=0.9)
        edges_txt = ", ".join(f"({p}, {c})" for p, c in case["edges"])
        self.set_caption(f"{len(case['all'])} nodos (= 2k − 1) y aristas {edges_txt}", C_EDGE)
        lens = [self.depth[c] - self.depth[p] for p, c in case["edges"]]
        self.set_caption(f"Subárbol que los une: {' + '.join(map(str, lens))} = {sum(lens)} aristas", C_QUERY)
        self.clear_caption()
        self.play(FadeOut(VGroup(h, tree, lbl, row, lines, *vls)))

    # ---------------- 11. costo ----------------
    def cost(self):
        h = Text("¿Cuánto cuesta?", font_size=34, weight=BOLD).to_edge(UP)
        rows = VGroup(
            Text("Preproceso, una sola vez:  O(n log n)", font_size=25),
            Text("Cada consulta:  O(k log k)   (O(k) si ya viene ordenada por tin)", font_size=25, color=C_EDGE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(rows).next_to(h, DOWN, buff=0.6)
        self.play(Write(h), run_time=0.8)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.3), run_time=0.5)
            self.wait(0.6)
        bench = load_bench()
        bars = VGroup()
        if bench:
            vt, full = bench
            maxw = 8.0
            def bar(label, val, col):
                b = Rectangle(width=max(0.06, maxw * val / full), height=0.45, color=col,
                              fill_color=col, fill_opacity=0.85, stroke_width=0)
                name = Text(label, font_size=20).next_to(b, LEFT, buff=0.25)
                num = Text(f"{val:,.0f} µs".replace(",", " "), font_size=20, color=col).next_to(b, RIGHT, buff=0.2)
                return VGroup(name, b, num)
            b1 = bar("virtual tree (k = 100)", vt, C_LCA)
            b2 = bar("recorrer el árbol", full, C_BAD)
            for b, y in ((b1, -0.6), (b2, -1.4)):
                b[1].move_to([0, y, 0]).align_to(np.array([-3.0, 0, 0]), LEFT)
                b[0].next_to(b[1], LEFT, buff=0.25)
                b[2].next_to(b[1], RIGHT, buff=0.2)
            bars = VGroup(b1, b2)
            self.set_caption(f"Medido con n = 10⁶: unas {full / vt:.0f} veces más rápido que recorrer el árbol", C_LCA)
            self.play(FadeIn(b1[0]), FadeIn(b2[0]),
                      GrowFromEdge(b1[1], LEFT), GrowFromEdge(b2[1], LEFT), run_time=1.2)
            self.play(FadeIn(b1[2]), FadeIn(b2[2]))
        self.clear_caption()
        self.play(FadeOut(VGroup(h, rows, bars)))

    # ---------------- 12. resumen y créditos ----------------
    def summary(self):
        self.show_slide("Resumen", [
            ("Ordenar por tin  →  LCA de vecinos  →  pila.", WHITE),
            ("≤ 2k − 1 nodos, en O(k log k).", C_EDGE),
            ("Cada consulta cuesta según k, no según n.", C_PATH),
        ], end=1.0)

    def credits(self):
        t = Text("Virtual Tree (Auxiliary Tree)", font_size=36, weight=BOLD)
        s = Text("CS2023 · UTEC · 2026-2", font_size=22, color=GRAY_B)
        m = VGroup(*[Text(x, font_size=26) for x in MEMBERS]).arrange(DOWN, buff=0.25)
        VGroup(t, s, m).arrange(DOWN, buff=0.5)
        self.play(FadeIn(VGroup(t, s, m)))
        self.wait(2.5)
        self.play(FadeOut(VGroup(t, s, m)))
