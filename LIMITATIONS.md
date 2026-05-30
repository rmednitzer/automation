# Limitations

Known scope boundaries and acknowledged gaps. Read alongside
[`README.md`](./README.md) and
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml).

| ID | State | Closure path |
|----|-------|--------------|
| L1 | Ubuntu 24.04 LTS only (each role's `meta/main.yml` declares noble) | Out of scope for the current fleet. Multi-distro would need role conditionals, a CI matrix, and per-distro Molecule scenarios. |
| L2 | First Molecule scenario landed for the `users` role (`roles/users/molecule/default/`); remaining roles still uncovered. CI gains a `molecule` matrix job and `make molecule`/`make molecule-deps` targets. **The scenario has not been executed in this environment (no Docker); it is authored and YAML/lint-validated only, and the CI `molecule` job is `continue-on-error` (non-gating) until it has a green run on a Docker host.** | Validate `make molecule` on a Docker-enabled host, drop the `continue-on-error` so it gates, then extend the matrix to `ssh_hardening`, `auditd`, and the rest. |
| L3 | Idempotency now exercised for `users` via Molecule's built-in idempotence step (`molecule test`), pending a Docker-enabled run. Other roles still rely on lint-enforced `changed_when`/`failed_when` only. | Expand the Molecule matrix (L2) so every role's converge is idempotence-tested. |
| L4 | Secrets-management not documented (`ansible-vault` expected but no worked example) | Document the secret-source convention in `CLAUDE.md`; add `inventories/<env>/group_vars/vault.yml.example`. |
| L5 | `sre_toolchain` lacks Molecule coverage (largest role, external binary downloads) | Molecule scenario verifying each binary installs, lands on PATH, and matches the expected version. The Molecule harness now exists (L2) so this is wiring a second scenario; network egress to GitHub releases makes it heavier than `users`. |
| L6 | `compliance-controls.yml` schema is informal; `scripts/validate-compliance-controls.py` enforces the convention but no published JSON Schema | Publish a JSON Schema under `docs/schemas/`; reference from the YAML header. |
| L7 | Pre-1.0, no release tags | Tag `0.1.0` once L2, L3, and L6 are closed. |
