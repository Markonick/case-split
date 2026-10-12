.PHONY: setup test lint

setup:  ## install deps (just pytest/ruff/mypy — pure Python, no DB)
	uv sync

# Deterministic, offline, key-free — no database, no Clerk.
test:
	uv run pytest -q

lint:
	uv run ruff check domain tests && uv run ruff format --check domain tests && uv run mypy domain
