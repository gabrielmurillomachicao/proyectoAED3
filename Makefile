# make test   -> compila y corre las pruebas del Virtual Tree (C++)
# make bench  -> mide tiempos (k fijo / n variable y n fijo / k variable)
# make trace  -> ejecuta el Virtual Tree real y escribe manim/trace.json
# make video  -> renderiza el video (1080p60) con Manim
# make informe -> compila informe/informe.pdf (requiere pdflatex)
CXX = g++ -std=c++17 -O2 -Wall
.PHONY: test bench trace video informe clean
test:
	cd cpp && $(CXX) tests.cpp -o tests && ./tests
bench:
	cd cpp && $(CXX) bench.cpp -o bench && ./bench | tee bench_result.csv
trace:
	cd cpp && $(CXX) trace_gen.cpp -o trace_gen && ./trace_gen > ../manim/trace.json
video: trace
	cd manim && manim -qh virtual_tree_scene.py VirtualTreeVideo
informe:
	cd informe && pdflatex -interaction=nonstopmode informe.tex && pdflatex -interaction=nonstopmode informe.tex
clean:
	rm -f cpp/tests cpp/trace_gen cpp/bench
	rm -rf manim/media
