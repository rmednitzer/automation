# ADR-006: AI-in-CI via local inference (advisory)

- **Status:** Proposed (dormant until a local inference endpoint is configured)
- **Date:** 2026-05-31
- **Deciders:** automation maintainers
- **Supersedes:** none
- **Related work:** the `ollama` role (POL-004 local inference); ADR-002
  (supply-chain); `scripts/ai-compliance-review.py`;
  `.github/workflows/ai-compliance-review.yml`.

## Context

The repository's compliance posture is enforced deterministically by
`scripts/validate-compliance-controls.py` (bidirectional role ↔ control
cross-references), which gates CI. That catches *structural* drift but not
*qualitative* gaps — e.g. a hardening rationale in a role header that the tasks
don't actually implement, or a control citation that is technically present but
semantically wrong.

An LLM is well suited to that qualitative review. The obvious implementation —
send the PR diff to a hosted AI API — would, however, **contradict the very
data-sovereignty principle** the `ollama` role and POL-004 exist to uphold:
source and compliance material would leave the estate for a third-party
processor on every PR.

## Decisions

### 1. AI review runs on LOCAL inference

The advisory review (`scripts/ai-compliance-review.py`) talks to a **local
Ollama endpoint** (`AI_REVIEW_OLLAMA_ENDPOINT`), not a hosted API. Diffs and the
control catalog never leave the estate — the same sovereignty stance as the
`ollama` role (GDPR Art 25 / Art 44). For real use it runs on a **self-hosted
runner** with network access to the local inference host.

### 2. Advisory and non-blocking

The job is **never a merge gate**. Any failure mode — no endpoint configured,
endpoint unreachable, empty response — is a graceful **skip with `exit 0`**, and
the step is `continue-on-error`. The deterministic validator remains the
authoritative gate, so CI stays reproducible and is never hostage to model
availability or nondeterminism. Findings are posted to the GitHub step summary.

### 3. Dormant by default

The workflow is gated on `vars.AI_REVIEW_OLLAMA_ENDPOINT`; with no endpoint
configured the job is **skipped entirely** (like the aspirational `redfish`
role). Enabling it is a deliberate, per-environment opt-in — set the variable
(and, for sovereignty, a self-hosted runner) and the review activates.

### 4. Stdlib only

The script uses only the Python standard library (`urllib`) against Ollama's
HTTP API — no third-party SDK, so it adds no CI supply-chain surface.

## Consequences

- **Sovereign AI-in-CI**: qualitative AI review without sending code to a hosted
  API — coherent with POL-004 and the `ollama` role.
- **Safe**: advisory-only; cannot break or flake CI; deterministic checks still
  gate.
- **Dormant today**: no effect until an endpoint is configured, so it adds no
  cost or noise to current runs.
- **Future work**: richer review scopes (task ↔ header consistency, sysctl/CIS
  drift), and reusing the same endpoint for other advisory checks.

## References

- ADR (this), the `ollama` role, POL-004 (`docs/compliance-controls.yml`).
- Ollama HTTP API (`/api/generate`).
- GDPR Art 25 (data protection by design), Art 44 (transfers); ISO/IEC
  27001:2022 A.8.9, A.8.28 (secure coding).
