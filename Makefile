# Development makefile for imgserve project

.PHONY: help build clean install dev-install run publish check twine-check

help:
	@echo "Common targets:"
	@echo "  make build        - Build sdist and wheel into dist/"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make install      - Install the built wheel (pip install dist/*.whl)"
	@echo "  make dev-install  - Editable install for development (pip install -e .)"
	@echo "  make run          - Run server in CWD (imgserve)"
	@echo "  make publish      - Upload to PyPI via twine"
	@echo "  make check        - Sanity check package metadata"
	@echo "  make twine-check  - Validate dist/ with twine"

build:
	python3 -m build

clean:
	rm -rf build dist *.egg-info **/*.egg-info

install:
	pip install --upgrade --force-reinstall dist/*.whl

dev-install:
	pip install -e .

run:
	imgserve --host=0.0.0.0 --port=8000

publish: build twine-check
	twine upload dist/*

check:
	python3 -c "import importlib.metadata as m;print(m.version('imgserve'))" || echo "Package not installed yet. Use 'make install' or 'make dev-install'"

twine-check:
	twine check dist/*

# Keep legacy target for generating an index for the non-CWD app
generate_index:
	python3 examples/indexed/generate_index.py \ 
		/home/daniel/backup/20250617_iMessage \ 
		examples/indexed/image_index.json
