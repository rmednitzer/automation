# Limitations

This document records known scope boundaries and acknowledged gaps. It is
read alongside [`README.md`](./README.md) and
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml). Each
limitation records:

- **State** — what is currently true
- **Implication** — what a reader must factor in
- **Closure path** — what would resolve it, if anything

## L1 — Ubuntu 24.04 LTS only

**State.** Roles are written and tested against Ubuntu 24.04 (noble). Each
role's `meta/main.yml` declares Ubuntu noble as the only supported
platform. No Debian, RHEL, Rocky, Alma, or SLES variants are exercised.

**Implication.** Running against other distributions is unsupported and may
silently miss hardening (e.g., `apt`-only package paths, Ubuntu-specific
defaults in `pam_faillock`, kernel parameter availability).

**Closure path.** Multi-distribution support is out of scope for the
current fleet. Closure would require role-level conditional branches, a CI
matrix, and corresponding Molecule scenarios.

## L2 — No Molecule role tests yet

**State.** None of the eleven roles ships a `molecule/` scenario. CI
verifies syntax (`ansible-playbook --syntax-check`) and static lint
(`ansible-lint` production profile), but not in-VM behavior or
idempotency.

**Implication.** Regressions are caught at PR review or in production, not
at CI time. Compliance claims rest on lint and manual review.

**Closure path.** Add `molecule/default/` to one role as a proof-of-concept
(candidate: `ssh_hardening` or `auditd`), wire `make molecule` into CI,
expand across roles. `make molecule` is already a placeholder in the
[`Makefile`](./Makefile).

## L3 — Idempotency not CI-tested

**State.** Roles aim to be idempotent (`changed_when` / `failed_when`
enforced by the `ansible-lint` production profile) but no CI gate runs the
playbook twice to verify zero changes on the second pass.

**Implication.** A role can pass lint and ship a defect that re-applies on
every run, polluting the audit trail and breaking the "stable state"
attestation.

**Closure path.** Add an idempotency job to CI gated on the existence of a
test inventory (Molecule with Docker, or a self-hosted runner). Depends on
L2.

## L4 — Secrets management is out of scope

**State.** The repository does not ship a secrets-management role.
Operators source secrets via `ansible-vault`, environment variables, or an
external secret manager (HashiCorp Vault, SOPS, AWS Secrets Manager). Vault
usage is not documented in `CLAUDE.md` beyond the precedence-rule note.

**Implication.** A first-time contributor may default to writing secrets
in plaintext under `host_vars/` or `group_vars/`. The pre-commit
`detect-private-key` hook catches the obvious cases but is not a
substitute for documented policy.

**Closure path.** Document the secret-source convention in `CLAUDE.md`
and add a worked example under
`inventories/<env>/group_vars/vault.yml.example`.

## L5 — `sre_toolchain` has no Molecule scenario

**State.** `sre_toolchain` is the largest role (multi-file task structure,
external binary downloads with checksum verification). It is also the most
prone to regression because upstream binary URLs and checksums change.

**Implication.** A toolchain update can silently install a stale or
unverified binary if a checksum is mis-typed.

**Closure path.** A Molecule scenario with a container image to verify
each binary installs, is on PATH, and is at the expected version. Depends
on L2.

## L6 — `compliance-controls.yml` schema is informal

**State.** `docs/compliance-controls.yml` follows a project-local
convention documented in `CLAUDE.md` and the file's own header comment.
[`scripts/validate-compliance-controls.py`](./scripts/validate-compliance-controls.py)
enforces the structural rules (top-level `controls:` / `policies:` keys,
required fields per entry, referenced role names exist), but no formal
JSON Schema is published.

**Implication.** External audit consumers must learn the local convention
to parse the file.

**Closure path.** Publish a JSON Schema under `docs/schemas/` and
reference it from the YAML header
(`# yaml-language-server: $schema=...`).

## L7 — No release tags yet

**State.** The repository is pre-1.0; commits ship into `main` without
versioned tags. CHANGELOG entries accumulate in `[Unreleased]`.

**Implication.** Downstream consumers cannot pin a release.

**Closure path.** Cut a 0.1.0 tag once Molecule is in CI for at least one
role (L2), idempotency is gated (L3), and the compliance-controls schema
is formalized (L6). Subsequent releases follow SemVer.
