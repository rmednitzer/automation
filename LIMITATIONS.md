# Limitations

Known scope boundaries and acknowledged gaps. Read alongside
[`README.md`](./README.md) and
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml).

| ID | State | Closure path |
|----|-------|--------------|
| L1 | Ubuntu 24.04 LTS only (each role's `meta/main.yml` declares noble). | Out of scope for the current fleet. Multi-distro would need role conditionals, a CI matrix, and per-distro Molecule scenarios. |
| L2 | No Molecule role tests; CI runs syntax + lint only. | Add `molecule/default/` to one role (candidate: `ssh_hardening` or `auditd`), wire `make molecule` into CI, expand across roles. Placeholder target already exists. |
| L3 | Idempotency not CI-tested. Lint enforces `changed_when`/`failed_when` but not behavior. | Idempotency job in CI gated on Molecule. Depends on L2. |
| L4 | Secrets-management not documented (`ansible-vault` expected but no worked example). | Document the secret-source convention in `CLAUDE.md`; add `inventories/<env>/group_vars/vault.yml.example`. |
| L5 | `sre_toolchain` lacks Molecule coverage (largest role, external binary downloads). | Molecule scenario verifying each binary installs, is on PATH, and is at the expected version. Depends on L2. |
| L6 | `compliance-controls.yml` schema is informal; `scripts/validate-compliance-controls.py` enforces the convention but no published JSON Schema. | Publish a JSON Schema under `docs/schemas/`; reference from the YAML header. |
| L7 | Pre-1.0, no release tags. | Tag `0.1.0` once L2, L3, and L6 are closed. |
