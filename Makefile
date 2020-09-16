TEST_PATHS := tests
SRC_PATHS := *.py docs/*.py i3pyblocks $(TEST_PATHS)
PYTHON := venv/bin/python
.PHONY: all deps lint \
	black black-fix clean deps-compile deps-upgrade deps-sync dev-install \
	docs isort isort-fix flake8 mypy test test-coverage

all: lint test-coverage
deps: deps-compile deps-sync
lint: black isort flake8 mypy
lint-fix: black-fix isort-fix

black:
	$(PYTHON) -m black --check $(SRC_PATHS)

black-fix:
	$(PYTHON) -m black $(SRC_PATHS)

clean:
	rm -rf *.egg-info .{mypy,pytest}_cache __pycache__

deps-compile:
	CUSTOM_COMPILE_COMMAND="make deps-compile"\
		$(PYTHON) -m piptools compile requirements/*.in -qo requirements.txt

deps-sync:
	$(PYTHON) -m piptools sync requirements.txt

dev-install:
	$(PYTHON) -m pip install -r requirements.txt

docs:
	cd docs && make html
	@echo -e "\033[95m\n\nBuild successful! View the docs homepage at docs/_build/html/index.html.\n\033[0m"

isort:
	$(PYTHON) -m isort --check $(SRC_PATHS)

isort-fix:
	$(PYTHON) -m isort $(SRC_PATHS)

flake8:
	$(PYTHON) -m flake8 $(SRC_PATHS)

mypy:
	$(PYTHON) -m mypy $(SRC_PATHS)

test:
	$(PYTHON) -m pytest $(TEST_PATHS)

test-coverage:
	$(PYTHON) -m pytest --cov=i3pyblocks --cov-report=term --cov-report=xml $(TEST_PATHS)
