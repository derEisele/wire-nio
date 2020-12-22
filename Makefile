PYTHON   ?= python

all:

test:
	python3 -m pytest --benchmark-disable

typecheck:
	mypy -p wire_nio --ignore-missing-imports --warn-redundant-casts

coverage:
	python3 -m pytest --cov wire_nio --benchmark-disable

isort:
	isort -p nio

clean:
	-rm -r dist/ __pycache__/
	-rm -r packages/

install:
	$(PYTHON) setup.py build
	$(PYTHON) setup.py install --skip-build -O1 --root=$(DESTDIR)


.PHONY: all clean test typecheck coverage
