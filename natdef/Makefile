# Nat Def — Strategic Threat & Posture briefing toolchain.
# Standard library only; there is nothing to install.

PYTHON ?= python3

.PHONY: help status render brief app validate strict check serve test all clean

help:
	@echo "make status    where the operation stands"
	@echo "make render    ledger -> the four generated pages"
	@echo "make brief     archive entry -> briefs/daily-brief-YYYY-MM-DD.html"
	@echo "make app       ledger -> natdef-console.html"
	@echo "make validate  the Step 6 gate"
	@echo "make strict    the Step 6 gate, failing on unregistered citations too"
	@echo "make check     render + console freshness + validator (run before committing)"
	@echo "make test      the test suite"
	@echo "make all       render, build the console, then check"
	@echo "make serve     serve the live ledger on localhost"

status:
	$(PYTHON) -m natdef status

render:
	$(PYTHON) -m natdef render

brief:
	$(PYTHON) -m natdef brief

app:
	$(PYTHON) -m natdef build-app

validate:
	$(PYTHON) -m natdef validate

strict:
	$(PYTHON) -m natdef validate --strict

check:
	$(PYTHON) -m natdef check

serve:
	$(PYTHON) -m natdef serve

test:
	$(PYTHON) -m unittest discover -s tests -t .

all: render app check

clean:
	rm -rf natdef/__pycache__ tests/__pycache__ .pytest_cache
