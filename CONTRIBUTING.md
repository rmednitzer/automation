# Contributing to automation

Thank you for contributing. This repository defines the **configuration and
hardening layer** for the fleet — what state each host should be in —
managed by Ansible. Infrastructure provisioning lives in
[`infra`](https://github.com/rmednitzer/infra); ad-hoc operator scripts live
in [`runbooks`](https://github.com/rmednitzer/runbooks).

## Before you start

- Read [`README.md`](./README.md) for regulatory scope, role inventory, and
  the evidence model.
- Read [`CLAUDE.md`](./CLAUDE.md) for Ansible style, FQCN policy, and
  variable precedence.
- Re-read [`docs/compliance-controls.yml`](./docs/compliance-controls.yml)
  if your change touches any hardening behavior — it is the source of truth
  for the regulation → control → role mapping.
- Check [`LIMITATIONS.md`](./LIMITATIONS.md) so you don't propose closing
  something already tracked as out of scope.

## Branch naming

- `feature/<short-description>` for new roles or playbooks
- `fix/<short-description>` for role corrections
- `compliance/<short-description>` for `docs/compliance-controls.yml`
  changes
- `chore/<short-description>` for CI / Makefile / lint updates
- `adr/<short-description>` for ADR-only changes (see `docs/`)

## Local development loop

```bash
# Install dependencies once.
pip install ansible-core ansible-lint yamllint pre-commit
ansible-galaxy install -r requirements.yml
pre-commit install

# Run everything CI runs.
make check

# Or individually:
make lint                  # yamllint + ansible-lint
make syntax-check          # ansible-playbook --syntax-check
make validate-compliance   # schema check on docs/compliance-controls.yml

# Dry-run a playbook against your inventory.
ansible-playbook -i inventories/development/hosts \
    playbooks/site-common.yml --check --diff
```

CI mirrors `make check`. PRs cannot merge with failing CI.

## Compliance-controls discipline

`docs/compliance-controls.yml` is the audit-facing artifact. Any change that
adds or removes a control, alters a regulatory mapping, or changes which
role implements a control **must**:

1. Update `docs/compliance-controls.yml` with the new mapping.
2. Update the affected role's `README.md` (variables, behavior, evidence).
3. Add an `[Unreleased]` entry in [`CHANGELOG.md`](./CHANGELOG.md)
   explicitly naming the CTL-/POL- IDs touched.
4. Pass `make validate-compliance`.

## Architecture Decision Records

Significant decisions (new role conventions, dropping a control, switching
a hardening source) are captured under [`docs/`](./docs/) using the
canonical Michael Nygard template (Status / Context / Decision /
Consequences).
[`docs/ADR-001-code-validation-baseline.md`](./docs/ADR-001-code-validation-baseline.md)
is the reference shape.

## Pull request expectations

Each PR should:

1. Update [`CHANGELOG.md`](./CHANGELOG.md) under `[Unreleased]`, citing any
   CTL-/POL- IDs touched.
2. Pass `make check` locally.
3. Pass CI (yamllint, ansible-lint, syntax-check, validate-compliance,
   pre-commit).
4. Use clear, imperative commit subjects (`Add auditd time-change rules`,
   `Fix ufw forwarding policy on noble`).
5. Cite the regulatory driver in the description when the change is
   compliance-motivated (`Closes NIS2 Art 21.2(e) gap`, etc.).

## Security-sensitive PRs

Changes touching `ssh_hardening`, `users`, `ufw`, `fail2ban`, `auditd`,
`rkhunter`, or `log_forwarding` require an explicit security review. Flag
them in the PR description. Never open a public issue for a suspected
vulnerability — see [`.github/SECURITY.md`](./.github/SECURITY.md).

## License

By contributing, you agree your contribution is licensed under
[Apache License 2.0](./LICENSE).
