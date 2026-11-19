# Virtual Tree (Auxiliary Tree) — animación

Proyecto Final 2 · CS2023 Algoritmos y Estructuras de Datos (UTEC, 2026-2).

Video educativo (estilo Manim) sobre el **Virtual Tree**: dado un árbol enraizado y
un subconjunto de `k` nodos, construye el árbol comprimido con esos nodos y los LCA
necesarios (a lo sumo `2k − 1` nodos), sin importar el tamaño `n` del árbol original.

## Integrantes
- Gabriel Murillo Machicao
- Juan Pablo Saavedra Ruiz

## Estructura del repositorio
```
cpp/virtual_tree.hpp     implementación propia (sin librerías de terceros)
cpp/tests.cpp            pruebas contra fuerza bruta
cpp/bench.cpp            medición empírica de tiempos
cpp/trace_gen.cpp        ejecuta la implementación y genera manim/trace.json
manim/virtual_tree_scene.py   escena que SOLO lee la traza y la dibuja
requirements.txt         dependencias de Python
```

## Cómo funciona
1. **Preprocesamiento** (`O(n log n)`): DFS iterativo con `tin/tout` (decide
   `es_ancestro(u, v)` en `O(1)`), Euler tour + Sparse Table (LCA en `O(1)`).
2. **`build_virtual(q)`** (`O(k log k)`): acepta la consulta en cualquier orden y con
   duplicados; ordena por `tin`, agrega el LCA de cada par adyacente, vuelve a ordenar
   y construye las aristas con una pila. Es la versión que se anima en el video.
3. **`build_virtual_sorted(q)`** (`O(k)`): si la consulta ya viene ordenada por `tin`
   y sin duplicados, inserta los LCA sobre la marcha en una sola pasada.
4. La animación se genera desde la traza real del paso 2 (incluido el Euler tour del
   DFS): ningún paso está escrito a mano.

## Guion del video (< 5 min, sin voz)
1. El problema y una pregunta concreta · 2. ¿Qué es? (TDA) · 3. `tin`/`tout` con el DFS
animado y una pregunta rápida · 4. LCA · 5. El algoritmo en 3 pasos · 6. Ejemplo completo
(pila visible en el árbol, cada decisión justificada, respuesta a la pregunta inicial) ·
7. ¿Por qué bastan los pares vecinos? (prueba visual) · 8. Caso borde · 9. **Tu turno** ·
10. Costo medido · 11. Resumen.

Cada subtítulo queda en pantalla al menos el tiempo de leerlo (15 caracteres/s). Para
auditarlo: `VT_CAPTION_LOG=subtitulos.json make video` guarda cada subtítulo con su tiempo.

## Requisitos
- `g++` con soporte C++17
- Python 3.10+ y [Manim Community](https://docs.manim.community) 0.22
  (`pip install -r requirements.txt`)
- Dependencias del sistema de Manim: Cairo, Pango y `ffmpeg`
  (en Ubuntu: `sudo apt install libcairo2-dev libpango1.0-dev ffmpeg`)

## Compilar y ejecutar
```bash
make test     # 3000 casos aleatorios x 2 variantes + consulta vacía + cadena de 10^6 nodos
make bench    # tiempos por consulta (escribe cpp/bench_result.csv)
make trace    # genera manim/trace.json desde C++
make video    # renderiza manim/media/videos/virtual_tree_scene/1080p60/VirtualTreeVideo.mp4
```

### Sin `make` (por ejemplo, en Windows)
En Windows se recomienda usar WSL (Ubuntu) y seguir los pasos anteriores. Si se tiene
`g++` (MSYS2/MinGW) y Manim instalados directamente en Windows, los mismos pasos son:
```bash
cd cpp
g++ -std=c++17 -O2 tests.cpp -o tests && ./tests              # pruebas
g++ -std=c++17 -O2 bench.cpp -o bench && ./bench               # mediciones
g++ -std=c++17 -O2 trace_gen.cpp -o trace_gen
./trace_gen > ../manim/trace.json                             # traza real
cd ../manim
manim -qh virtual_tree_scene.py VirtualTreeVideo               # video 1080p60
```
El video queda en `manim/media/videos/virtual_tree_scene/1080p60/VirtualTreeVideo.mp4`.
