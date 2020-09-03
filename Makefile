SRC_PATHS := i3pyblocks tests example.py
TEST_PATHS := tests
PYTHON := venv/bin/python
.PHONY: clean dev-install format format-check lint mypy tests tests-with-coverage

all: run

clean:
	git clean -fxd

tests:
	$(PYTHON) -m pytest $(TEST_PATHS)

tests-with-coverage:
	$(PYTHON) -m pytest --cov=i3pyblocks --cov-report=term --cov-report=xml $(TEST_PATHS)

format:
	$(PYTHON) -m black $(SRC_PATHS)

format-check:
	$(PYTHON) -m black --check $(SRC_PATHS)

isort:
	$(PYTHON) -m isort $(SRC_PATHS)

lint:
	$(PYTHON) -m flake8 $(SRC_PATHS)

mypy:
	$(PYTHON) -m mypy $(SRC_PATHS)

dev-install:
	$(PYTHON) -m pip install -r requirements.txt

deps: deps-compile deps-sync

deps-compile:
	CUSTOM_COMPILE_COMMAND="make deps-compile"\
		$(PYTHON) -m piptools compile requirements/*.in -qo - |\
		sed 's|^-e .*$$||g' |\
		tee requirements.txt

deps-upgrade:
	CUSTOM_COMPILE_COMMAND="make deps-compile"\
		$(PYTHON) -m piptools compile -U requirements/*.in -qo - |\
		sed 's|^-e .*$$||g' |\
		tee requirements.txt

deps-sync:
	$(PYTHON) -m piptools sync requirements.txt

run:
	$(PYTHON) "./run.py"
