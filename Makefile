# Makefile — automation repository.
# Run `make help` for the available targets.

SHELL := /usr/bin/env bash

.PHONY: help install lint syntax-check validate-compliance check molecule molecule-sre molecule-deps clean

# Roles that ship a molecule/default scenario. Each scenario tests both
# Ubuntu 24.04 (noble) and 26.04 (resolute) — see ADR-004. Requires Docker.
MOLECULE_ROLES := users ssh_hardening auditd common

# sre_toolchain ships a molecule scenario too, but it needs outbound network
# egress to the GitHub API + release CDN (and ideally SRE_TOOLCHAIN_GITHUB_TOKEN
# to dodge the 60-req/hour limit), so it is kept OUT of the default `molecule`
# target and CI matrix. Run it explicitly with `make molecule-sre`.
MOLECULE_ROLES_EGRESS := sre_toolchain

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

molecule:  ## Run Molecule scenarios (requires Docker): users ssh_hardening auditd common.
	@for role in $(MOLECULE_ROLES); do \
		echo "== molecule test: $$role =="; \
		( cd roles/$$role && molecule test ) || exit 1; \
	done

molecule-sre:  ## Run the egress-heavy sre_toolchain Molecule scenario (Docker + GitHub egress).
	@for role in $(MOLECULE_ROLES_EGRESS); do \
		echo "== molecule test: $$role =="; \
		( cd roles/$$role && molecule test ) || exit 1; \
	done

clean:  ## Remove transient caches.
	rm -rf .ansible/ .yamllint.cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
