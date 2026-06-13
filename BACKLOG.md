# Backlog — deferred and tracked work

Deferred items raised by the 2026-06-13 audit pass. All are defense-in-depth
hardening of *default postures* where the secure mechanism already exists and is
enforced when enabled; none is an active vulnerability. They are deferred rather
than fixed inline because each is either a deliberate opt-in design choice (not
to be silently overridden), needs an authoritative external constant (a GPG
fingerprint) that must be verified out of band, or cannot be test-covered in the
audit environment (no Docker/Molecule). Close an item by linking the PR/commit
that resolves it and moving it to **Resolved**.

## Open

### Security / supply-chain hardening

| Id | Item | Origin | Severity | Effort | Suggested approach | Owner |
|----|------|--------|----------|--------|--------------------|-------|
| A-1 | Pin the Wazuh APT key fingerprint by default (`roles/wazuh_agent`) | [audit/02](audit/02-security-findings.md) | low | S | Set `wazuh_apt_key_fingerprint` to the published Wazuh GPG fingerprint (verified against an authoritative Wazuh source) so the existing fail-closed assertion runs by default; document the rotation process. | platform/security |
| A-2 | Pin the Vector/Datadog APT key fingerprint(s) by default (`roles/vector`) | [audit/02](audit/02-security-findings.md) | low | S | Same as A-1 for `vector_apt_key_fingerprints` (verified against Datadog's published key). Folds with A-1. | platform/security |
| A-3 | Narrow the sre_toolchain cosign certificate-identity regexp per tool | [audit/02](audit/02-security-findings.md) | low | M | Replace the catch-all `^https://github.com/.+/.github/workflows/.+@.+` with per-tool identity regexps (e.g. `^https://github.com/cli/cli/\.github/workflows/`). Only affects runs with `sre_toolchain_verify_signatures: true`. Needs per-tool research + an accept/reject test. | platform/security |
| A-4 | Integrity-verify kubectx/kubens under `best-effort` checksum policy | [audit/02](audit/02-security-findings.md) | low | M | When `sre_toolchain_verify_signatures: true`, verify the asset against the cosign-attested release digest instead of installing unverified; otherwise keep the strict-policy skip. | platform/security |
| A-5 | Tighten the Ollama temp-archive mode (`roles/ollama/tasks/main.yml:104`) | [audit/02](audit/02-security-findings.md) | low (nit) | S | Use `0600` (or a `0700` scratch dir, mirroring `sre_toolchain`). Pair with an `ollama` Molecule scenario so the change is test-covered (the reason it was not done inline this pass). | platform/SRE |

## Resolved

_None yet (backlog opened 2026-06-13)._
