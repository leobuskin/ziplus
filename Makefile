VENV := .venv/bin
SRC  := ziplus/ tests/ scripts/

export VIRTUAL_ENV := $(CURDIR)/.venv

.PHONY: format lint typecheck test all

format:
	$(VENV)/ruff check --select I --fix $(SRC)
	$(VENV)/ruff format $(SRC)

lint:
	$(VENV)/ruff check $(SRC)
	$(VENV)/ruff format --check $(SRC)

typecheck:
	$(VENV)/ty check ziplus/ tests/

test:
	$(VENV)/pytest --cov=ziplus --cov-fail-under=100

all: format lint typecheck test
