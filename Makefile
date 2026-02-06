.PHONY: test test-all test-int lint typecheck pin-ruff verify-bugs

test:
	uv run pytest tests/unit/ -v

test-all:
	uv run pytest tests/ -v

test-int:
	uv run pytest tests/integration/ -v

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run mypy src/ate/

pin-ruff:
	bash scripts/pin_ruff.sh

verify-bugs:
	uv run python scripts/verify_bugs.py
