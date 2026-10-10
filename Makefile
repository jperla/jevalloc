.PHONY: all allocator test benchmarks extras clean
all: allocator benchmarks
allocator:
	cmake -S . -B build
	cmake --build build -j 4
benchmarks:
	python3 tools/build_bench.py
extras: benchmarks
	python3 tools/extras.py
test: all
	python3 tests/test.py
clean:
	rm -rf build
