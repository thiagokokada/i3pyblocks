SRC_PATHS := i3pyblocks tests run.py
.PHONY: tests clean format lint mypy

all: run

clean:
	git clean -fxd

tests:
	poetry run pytest

format:
	poetry run black $(SRC_PATHS)

lint:
	poetry run flake8 $(SRC_PATHS)

mypy:
	poetry run mypy $(SRC_PATHS)

run:
	@poetry run "./run.py"
