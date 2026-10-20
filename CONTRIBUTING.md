# Contributing to `automation`

Configuration and hardening layer for the fleet — what state each host
should be in — managed by Ansible. Conventions in
[`CLAUDE.md`](./CLAUDE.md); compliance mappings in
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml). This
file is workflow only.

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

1. `[Unreleased]` entry in [`CHANGELOG.md`](./CHANGELOG.md), citing any
   CTL-/POL- IDs touched.
2. `make check` passes locally.
3. **Compliance change** — touching `docs/compliance-controls.yml`,
   regulatory mappings, or which role covers a control: update
   `docs/compliance-controls.yml`, the affected role's `README.md`, and
   name the IDs in the changelog entry.
4. **Decision that changes a convention** — drop a control, switch a
   hardening source, etc.: add an ADR using the Michael Nygard template.
   [`docs/ADR-001-code-validation-baseline.md`](./docs/ADR-001-code-validation-baseline.md)
   is the reference shape.

PR template:
[`.github/PULL_REQUEST_TEMPLATE.md`](./.github/PULL_REQUEST_TEMPLATE.md).
Suspected vulnerabilities — see
[`.github/SECURITY.md`](./.github/SECURITY.md); never open a public
issue.

By contributing, you agree your contribution is licensed under
[Apache License 2.0](./LICENSE).


## Dependency automation

Renovate policy is owned by this repository in `renovate.json5`. It does not
inherit another project’s policy. Keep update grouping, release-age delays,
major-version review and lock-maintenance behavior explicit here. Built-in
Renovate presets supply standard defaults; repository-specific decisions remain
local. Review policy changes and actual dependency extraction before merging.


## CI run ownership

The PR-validation workflows updated here coalesce first attempts for the same PR.
Manual reruns use separate run-ID/attempt groups, so rerunning an old revision
cannot cancel or replace current-head validation. Non-PR invocations also use
unique run-ID/attempt groups to preserve each revision's evidence.
GitHub does not guarantee chronological ordering of initial attempts: a late event
can still interrupt another initial attempt. Required checks bind to the current
head; a cancelled current-head check needs a successful rerun before merge.
Explicit diagnostic/publication serialization in other workflows remains separate. Reusable
workflows have distinct file prefixes to avoid cancelling a caller or sibling.
Cancelling an obsolete PR run is not a successful check; the current head still
needs all required results. Revision identity and signing gates remain separate.
Publication workflows retain their existing serialization and cache isolation.
Revert this repository's workflow change to restore the earlier scheduling;
no service deployment or application-data migration is involved.
