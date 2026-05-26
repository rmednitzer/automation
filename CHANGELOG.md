# Changelog

Format: [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

PRs touching roles, playbooks, or
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml) must add
an `[Unreleased]` entry naming affected CTL- / POL- IDs.

## [Unreleased]

- Optimise and rewrite every `.md` file end-to-end for tighter prose,
  consistent voice, and uniform structure across the three companion
  repos: `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `LIMITATIONS.md`,
  `.github/SECURITY.md`, `.github/PULL_REQUEST_TEMPLATE.md`,
  `.github/copilot-instructions.md`, `docs/ADR-001-code-validation-baseline.md`,
  and all 11 `roles/<role>/README.md` files
  (`common`, `users`, `ntp`, `ssh_hardening`, `ufw`, `fail2ban`,
  `aide`, `rkhunter`, `log_forwarding`, `auditd`, `sre_toolchain`).
  ADR Status / Deciders / Findings / Decisions shape preserved; all
  factual content — defaults, variable descriptions, compliance
  mappings, F1–F4 finding categorisation, accepted design tensions
  F3.1–F3.6 — preserved verbatim. No role behaviour change, no
  playbook change, no `docs/compliance-controls.yml` change. No
  CTL-/POL- IDs touched. `make check` passes:
  `0 failure(s), 0 warning(s)`; `OK: 3 control(s), 5 policy(ies);
  roles cross-referenced against 11 role(s)`.
- Remove empty global `files/`, `templates/`, `host_vars/`, and
  `plugins/{filter,lookup,modules}/` stub directories — these are not part
  of the official Ansible best-practices layout (role-scoped `files/` /
  `templates/` are; top-level ones are not), were never populated, and
  would not be loaded without explicit `ansible.cfg` plugin paths. Per-env
  `inventories/<env>/group_vars/` and `inventories/<env>/host_vars/` are
  retained as documented extensibility points. `CLAUDE.md` and `README.md`
  Repository Structure sections updated to match. No role, playbook, or
  `docs/compliance-controls.yml` change; no CTL- / POL- IDs touched.
- Sync governance docs (SECURITY policy shape, PR template structure,
  copilot instructions, README Companion repositories pointer) with the
  companion `runbooks` and `infra` repos. No role, playbook, or
  `docs/compliance-controls.yml` change; no CTL- / POL- IDs touched.

## [0.0.0]

### Scaffolding (PR #18)

- Governance: `NOTICE`, `CHANGELOG.md`, `CONTRIBUTING.md`,
  `LIMITATIONS.md`, `.github/CODEOWNERS`, `.editorconfig`.
- `Makefile` (`help`, `install`, `lint`, `syntax-check`,
  `validate-compliance`, `check`, `molecule` placeholder, `clean`).
- `scripts/validate-compliance-controls.py` — structural check on
  `docs/compliance-controls.yml` + role cross-reference.
- `.pre-commit-config.yaml` running yamllint, ansible-lint (production
  profile), EditorConfig, hygiene.
- CI: `validate-compliance` and `pre-commit` jobs added.

### Initial Ansible structure

- 11 roles: `common`, `users`, `ntp`, `ssh_hardening`, `ufw`,
  `fail2ban`, `aide`, `rkhunter`, `log_forwarding`, `auditd`,
  `sre_toolchain`.
- `playbooks/site-common.yml` (fleet baseline) and
  `playbooks/sre-toolchain.yml` (operator hosts).
- 3-environment inventory scaffolding under `inventories/`.
- `docs/compliance-controls.yml` mapping CTL- / POL- IDs to NIS2 Art
  21–23, GDPR Art 5/25/32, ISO 27001 A.5–A.8, CRA Annex I, NISG 2026.
- ADR-001 — code-validation baseline (2026-05-24).
- CI: yamllint, ansible-lint (production profile), playbook syntax-check.
- `.github/SECURITY.md`, PR / issue templates, Dependabot.
