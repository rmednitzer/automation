# Contributing to automation

This repository defines the **configuration and hardening layer** for
the fleet — what state each host should be in — managed by Ansible.
Conventions live in [`CLAUDE.md`](./CLAUDE.md); compliance mappings in
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml). This
file covers workflow only.

## Branch naming

| Prefix | Use |
|--------|-----|
| `feature/` | New roles or playbooks |
| `fix/` | Role corrections |
| `compliance/` | `docs/compliance-controls.yml` changes |
| `chore/` | CI / Makefile / lint |
| `adr/` | ADR-only changes (`docs/`) |

## Local loop

```bash
make install   # ansible-core, ansible-lint, yamllint, pre-commit, galaxy
make check     # lint + syntax-check + validate-compliance
pre-commit install && pre-commit run --all-files
```

CI mirrors `make check` plus a pre-commit hygiene job. PRs cannot merge
with failing CI.

## Pull request expectations

1. Update [`CHANGELOG.md`](./CHANGELOG.md) under `[Unreleased]`, citing
   any CTL- / POL- IDs touched.
2. Pass `make check` locally.
3. **Compliance change** (touching `docs/compliance-controls.yml`,
   regulatory mappings, or which role covers a control): update
   `docs/compliance-controls.yml`, the affected role's `README.md`, and
   name the IDs in the changelog entry.
4. **Decision that changes a convention** (drop a control, switch a
   hardening source): add an ADR using the Michael Nygard template.
   [`docs/ADR-001-code-validation-baseline.md`](./docs/ADR-001-code-validation-baseline.md)
   is the reference shape.

Suspected vulnerabilities: [`.github/SECURITY.md`](./.github/SECURITY.md) —
never open a public issue.

By contributing, you agree your contribution is licensed under
[Apache License 2.0](./LICENSE).
