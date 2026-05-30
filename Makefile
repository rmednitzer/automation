# Makefile — automation repository.
# Run `make help` for the available targets.

SHELL := /usr/bin/env bash

.PHONY: help install lint syntax-check validate-compliance check molecule molecule-deps clean

# Roles that ship a molecule/default scenario.
MOLECULE_ROLES := users

PLAYBOOKS := $(wildcard playbooks/*.yml)

help:  ## Show this help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install runtime + lint dependencies and Galaxy collections.
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt
	ansible-galaxy install -r requirements.yml

lint:  ## Run yamllint + ansible-lint (production profile).
	yamllint .
	ansible-lint

syntax-check:  ## Run `ansible-playbook --syntax-check` on every playbook.
	@for pb in $(PLAYBOOKS); do \
		echo "Checking $$pb..."; \
		ansible-playbook "$$pb" --syntax-check; \
	done

validate-compliance:  ## Schema-check docs/compliance-controls.yml + verify role refs.
	python3 scripts/validate-compliance-controls.py

check: lint syntax-check validate-compliance  ## Lint + syntax-check + compliance schema.

molecule-deps:  ## Install Molecule + the Docker driver.
	pip install "molecule>=6" "molecule-plugins[docker]" docker

molecule:  ## Run Molecule scenarios (requires Docker). Currently: users.
	@for role in $(MOLECULE_ROLES); do \
		echo "== molecule test: $$role =="; \
		( cd roles/$$role && molecule test ) || exit 1; \
	done

clean:  ## Remove transient caches.
	rm -rf .ansible/ .yamllint.cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
