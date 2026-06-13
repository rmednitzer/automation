# Phase 1 — Validation baseline (`automation`)

Audit pass: `audit/2026-06-13-full-pass`. Read-only phase. Regression
reference for any later change. All commands run this session against branch
base `de71281`. `ansible-core` and the pinned Galaxy collections were installed
this session so the gates are executed, not inferred.

## Lint

```
$ yamllint .            -> exit 0  (clean)
$ ansible-lint          -> Passed: 0 failure(s), 0 warning(s) in 193 files
                           processed of 255 encountered. Profile 'production'
                           was required, and it passed.
```

Result: **clean** on both. ansible-lint 26.4.0 matches the CI pin.

## Syntax check

`ansible-playbook <pb> --syntax-check` per playbook:

| Playbook | Result |
|----------|--------|
| `playbooks/local-inference.yml` | parses OK |
| `playbooks/redfish-oob.yml` | parses OK |
| `playbooks/site-common.yml` | parses OK |
| `playbooks/sre-toolchain.yml` | parses OK |

Result: **4/4 parse cleanly.**

`[UNVERIFIED]` delta: syntax-check ran on `ansible-core 2.19.10` (the version
ansible-lint pulled in) whereas CI pins `2.21.0`. The parser surface for these
playbooks is stable across that minor delta; CI runs the pinned version. Treat
the local pass as a strong but not version-identical signal.

## Compliance validation

```
$ python3 scripts/validate-compliance-controls.py
OK: 3 control(s), 5 policy(ies); roles cross-referenced against 22 role(s);
bidirectional header cross-references consistent; all 5 declared frameworks
mapped; derived indexes in sync; schema present (jsonschema not installed —
structural check authoritative).
```

Result: **OK.** (jsonschema was not on PATH for this run, so the validator's
structural checks were authoritative; CI additionally runs the JSON Schema
check with `jsonschema==4.26.0` installed.)

## Vault convention

```
$ bash scripts/check-vault-encrypted.sh <tracked vault.yml files>   -> exit 0
```

Tracked vault files: `docs/examples/vault.yml` (really ansible-vault encrypted)
and `inventories/development/group_vars/vault.yml.example` (a plaintext
placeholder, exempt by the `.example` suffix). The guard passed. CI's
`vault-example` job additionally proves the encrypted example decrypts with the
documented throwaway password.

## Security tooling (cross-referenced in Phase 2)

| Tool | Command | Result |
|------|---------|--------|
| gitleaks (history) | `gitleaks detect --redact` | 49 commits scanned, **no leaks** |
| gitleaks (working tree, tracked) | `gitleaks detect` (git-tracked content) | **no leaks** |

Note: a `gitleaks detect --no-git` over the *whole* working tree reported 130
hits, but **all 130 are under the locally-installed, gitignored `collections/`
directory** (third-party Galaxy collection test fixtures with fake secrets),
which is absent in a clean CI checkout and excluded by `.gitleaks.toml`. The
git-history scan (which covers all committed content) is **0 leaks**, so the
tracked tree is clean. Verified by bucketing the report by top-level directory:
130/130 under `collections/`.

## Not run in this environment

- **Molecule** (4-role matrix, dual-OS): requires Docker, which is unavailable
  here. CI gates on it (LIMITATIONS L2). Recorded as a baseline gap; the
  scenarios are unchanged by this pass.

## Baseline summary

| Gate | Result |
|------|--------|
| yamllint | clean |
| ansible-lint (production) | Passed (193 files) |
| syntax-check (x4) | 4/4 parse |
| validate-compliance | OK |
| vault-encrypted guard | pass |
| gitleaks (tracked/history) | 0 |
| Molecule | not run (no Docker); CI-gated |

The repository is **green across every gate reproducible in this environment.**
