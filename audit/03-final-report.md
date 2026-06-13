# Audit final report — `automation` (2026-06-13)

Branch: `audit/2026-06-13-full-pass`. Base: `de71281` (#59).

## Executive summary

`automation` is a mature, compliance-aligned Ansible hardening repo in a
**verified-clean state**. The full gate suite is green, and a line-level review
of the Python/shell scripts, both CI workflows, and all 22 roles found **no
critical or high findings and no active vulnerabilities**. The five findings
raised are all defense-in-depth — *default postures* that could be stronger,
where the secure mechanism already exists and is enforced when enabled. **No
source files were changed**: each finding is either a deliberate opt-in design
choice, needs an authoritative external constant verified out of band, or cannot
be test-covered without Docker/Molecule (unavailable here). All five are tracked
in `BACKLOG.md`.

## Baseline vs post-pass metrics

No fixes were made, so baseline equals post-pass.

| Metric | Baseline | Post-pass |
|--------|----------|-----------|
| yamllint | clean | clean |
| ansible-lint (production) | Passed (193 files) | Passed |
| syntax-check | 4/4 parse | 4/4 |
| validate-compliance | OK | OK |
| vault-encrypted guard | pass | pass |
| gitleaks (history + tracked) | 0 | 0 |
| Security findings | 0 critical/high; 5 low (deferred) | unchanged |
| Molecule | not run (no Docker); CI-gated | n/a |

## Commits in this pass

| Commit | Rationale |
|--------|-----------|
| `78fdcfb` | `docs:` Phase 0/1 inventory + baseline |
| (this commit) | `docs:` findings register, backlog, final report |

No `fix:`/`security:` commits — see the rationale above and per-finding
dispositions in `02-security-findings.md`.

## Residual risk statement

Residual risk is **low**. The findings are hardening of opt-in defaults
(`wazuh_agent`/`vector` fingerprint pins, sre_toolchain cosign identity scope,
best-effort kubectx integrity, ollama temp-archive mode). In every case the
secure path is available and enforced when enabled, downloads on the default
path are checksum-verified, and the affected roles (`wazuh_agent`, `vector`,
`ollama`) are opt-in (outside the default `site-common.yml` baseline). The
deliberately-strong baseline (ssh_hardening, users, redfish, the compliance
scripts, both workflows) was reviewed and confirmed clean.

A small confidence caveat: `syntax-check` ran on `ansible-core 2.19.10` locally
vs the CI pin `2.21.0`, and the Molecule matrix could not run here (no Docker).
CI is authoritative for both.

## Top 5 backlog items

1. **A-1** — Pin the Wazuh APT key fingerprint by default (low, S).
2. **A-2** — Pin the Vector/Datadog APT key fingerprint by default (low, S).
3. **A-3** — Narrow the sre_toolchain cosign identity regexp per tool (low, M).
4. **A-4** — Verify kubectx/kubens under best-effort checksum policy (low, M).
5. **A-5** — Tighten the ollama temp-archive mode + add a Molecule scenario (low, S).

## Stop conditions

None encountered. The gate suite runs; no secrets in tree or history; no fix
required a major version bump or migration; the `ai-compliance-review` workflow
and PR-content paths were reviewed and do not let untrusted input reach a
privileged sink; no untrusted repo content attempted to redirect the audit.
