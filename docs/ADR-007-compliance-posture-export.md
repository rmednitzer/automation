# ADR-007: Compliance posture export as the fleet → MCP bridge

- **Status:** Accepted (export implemented; the serving gateway is external)
- **Date:** 2026-05-31
- **Deciders:** automation maintainers
- **Supersedes:** none
- **Related work:** ADR-006 (AI-in-CI via local inference); POL-004;
  `scripts/export-compliance-posture.py`;
  `scripts/validate-compliance-controls.py`.

## Context

The AI layer (the Vertex MCP gateway and the local-inference workflows) needs to
reason about the fleet's compliance posture — which controls/policies exist,
what regulation each maps to, which roles implement them, and which roles are in
the baseline. That knowledge lives in `docs/compliance-controls.yml` and
`playbooks/site-common.yml`.

Letting the AI layer parse those Ansible/YAML sources directly is brittle
(couples the AI side to repo internals and Ansible semantics) and risks leaking
more than intended (inventory, host vars, secrets). We want a **stable,
minimal, machine-readable contract** between the fleet and the AI layer.

## Decisions

### 1. Publish a versioned JSON artifact

`scripts/export-compliance-posture.py` emits a single JSON document
(`schema: fleet-compliance-posture/v1`) with the controls, policies, their
regulatory mappings, the implementing roles, a per-role view (which
controls/policies it implements, whether it is in the baseline and whether
gated by a condition), and framework/summary tallies. The schema field lets the
contract evolve without breaking consumers.

### 2. Read-only, one-way, and safe to serve

The export is **fleet → AI only**, and reshapes data that
`validate-compliance-controls.py` has already proven consistent — that validator
stays the source of truth; this script never mutates anything. It exposes
**only** compliance metadata (controls/policies/roles/regulatory mappings +
baseline membership) — no inventory, host vars, or secrets — so the artifact is
safe for the gateway to serve.

### 3. Deterministic output

Output is sorted and carries **no embedded timestamp**, so it is reproducible
and diffable; CI smoke-tests that it stays valid JSON. The serving layer adds
its own served-at metadata.

### 4. The gateway serves it; the contract lives here

The MCP gateway obtains the artifact (regenerate-on-demand via the script, or a
CI-published copy) and exposes it to the AI layer. The gateway/serving side
lives on Vertex, **outside** this repository — this ADR defines the contract and
the producer, not the server, keeping the fleet↔MCP boundary explicit.

## Consequences

- The AI layer reasons about compliance through a stable JSON contract, not by
  parsing Ansible — decoupled and safe.
- Versioned schema allows additive evolution (e.g. per-host role application
  from inventories, or an MCP tool wrapping the export) without breaking
  consumers.
- One more reason to keep the catalog and role headers consistent — the export
  (and thus the AI layer's view) is only as good as `compliance-controls.yml`,
  which the validator already guards.

## References

- ADR-006 (AI-in-CI via local inference); the `ollama` role / POL-004.
- `scripts/export-compliance-posture.py`, `make export-compliance`.
- GDPR Art 5(2) accountability; ISO/IEC 27001:2022 A.5.36 (compliance review).
