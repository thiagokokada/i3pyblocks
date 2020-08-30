SRC_PATHS := i3pyblocks tests run.py
.PHONY: tests clean format lint mypy

all: run

clean:
	git clean -fxd

tests:
	poetry run python3 -m pytest tests

format:
	poetry run black $(SRC_PATHS)

lint:
	poetry run flake8 $(SRC_PATHS)

mypy:
	poetry run mypy $(SRC_PATHS)

deps:
	poetry lock
	poetry export -f requirements.txt -E all_deps -o requirements.txt
	poetry export -f requirements.txt --dev -o requirements-dev.txt

run:
	@poetry run "./run.py"
