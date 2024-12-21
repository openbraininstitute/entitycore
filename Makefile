format:
	uv run -m ruff format
	uv run -m ruff check --fix

lint:
	uv run -m ruff format --check
	uv run -m ruff check
	uv run -m mypy app
