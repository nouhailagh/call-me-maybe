install:
	uv sync

run:
	uv run python -m src

debug:
	uv run python -m src --pdb

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

clean:
	rm -rf __pycache__ .mypy_cache