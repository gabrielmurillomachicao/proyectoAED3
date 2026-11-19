# make bench  -> mide tiempos (k fijo / n variable y n fijo / k variable)
# make trace  -> ejecuta el Virtual Tree real y escribe manim/trace.json
# make video  -> renderiza el video (1080p60) con Manim
CXX = g++ -std=c++17 -O2 -Wall
.PHONY: bench trace video clean
bench:
	cd cpp && $(CXX) bench.cpp -o bench && ./bench | tee bench_result.csv
trace:
	cd cpp && $(CXX) trace_gen.cpp -o trace_gen && ./trace_gen > ../manim/trace.json
video: trace
	cd manim && manim -qh virtual_tree_scene.py VirtualTreeVideo
clean:
	rm -f cpp/trace_gen cpp/bench
	rm -rf manim/media
