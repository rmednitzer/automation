# Changelog

All notable changes to this project will be documented in this file.

Format: [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Compliance audits (NIS2 Art 23, GDPR Art 33–34, CRA vulnerability reporting)
rely on an accurate change history. PRs touching roles, playbooks, or
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml) must add an
`[Unreleased]` entry citing any affected control or policy IDs.

## [Unreleased]

### Added

- `NOTICE` file for Apache 2.0 source-distribution conformance.
- `.editorconfig` for consistent indentation across editors.
- `.pre-commit-config.yaml` orchestrating `ansible-lint` (production
  profile), `yamllint`, `editorconfig-checker`, and standard hygiene hooks;
  mirrored in CI.
- `Makefile` exposing `make help`, `make lint`, `make syntax-check`,
  `make validate-compliance`, `make check`, and a `make molecule`
  placeholder for the pending role-test wave (`LIMITATIONS.md` L2).
- `scripts/validate-compliance-controls.py` enforces the structural rules
  of `docs/compliance-controls.yml` (control / policy IDs, required fields,
  regulatory mapping cardinality) and cross-references each `roles:` entry
  against the `roles/` directory; runs in CI.
- `LIMITATIONS.md` documenting known scope boundaries (Ubuntu 24.04 only,
  no Molecule role tests yet, idempotency not CI-gated, secrets-management
  out of scope, …).
- `CONTRIBUTING.md` defining the contribution workflow, branch naming, the
  compliance-controls update obligation, and ADR expectations.
- `.github/CODEOWNERS` assigning review responsibility for roles,
  compliance docs, scripts, and workflows.
- This `CHANGELOG.md`.

### Changed

- `.github/workflows/ci.yml` adds a `validate-compliance` job invoking the
  new schema check, and a `pre-commit` job running the full hook set
  against changed files.
- `README.md` indexes the new governance and tooling files.

## [0.0.0] — initial Ansible structure (post-rename)

- Repository renamed from `ansible-ops` to `automation`.
- Eleven roles in `roles/`: `common`, `users`, `ntp`, `ssh_hardening`,
  `ufw`, `fail2ban`, `aide`, `rkhunter`, `log_forwarding`, `auditd`,
  `sre_toolchain`.
- `playbooks/site-common.yml` (fleet hardening baseline) and
  `playbooks/sre-toolchain.yml` (operator hosts).
- Three-environment inventory scaffolding under `inventories/`
  (production, staging, development).
- `docs/compliance-controls.yml` mapping internal controls (CTL-NNN) and
  ISMS policies (POL-NNN) to NIS2 Art 21–23, GDPR Art 5 / 25 / 32,
  ISO 27001 A.5–A.8, CRA Annex I, NISG 2026, with role-coverage
  attribution.
- ADR-001 — code-validation baseline (2026-05-24), pinning the
  `ansible-lint` production profile and recording known-good source
  references (CIS Ubuntu Benchmark, BSI TR-02102-4, upstream OpenSSH /
  chrony / auditd / `pam_faillock` / `pam_pwquality` documentation).
- CI: yamllint, ansible-lint, playbook syntax-check.
- `.github/SECURITY.md`, PR / issue templates, Dependabot.
