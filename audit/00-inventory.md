# Phase 0 — Recon and inventory (`automation`)

Audit pass: `audit/2026-06-13-full-pass`. Read-only phase. Branch base:
`de71281` ("Run Molecule live, fix surfaced role bugs, gate the matrix on
push/PR (L2)", #59).

Every figure below was produced by a command run in this session. Items not
verifiable this session are tagged `[UNVERIFIED]`.

## Component map

Ansible automation: a compliance-aligned hardening baseline plus operator-host
and out-of-band roles. No compiled artifact; the "build" is
yamllint + ansible-lint + syntax-check + the compliance validators, and the
"tests" are Molecule scenarios (Docker, dual-OS noble + resolute).

```
automation/
├── roles/                22 roles (19 baseline + sre_toolchain, ollama, redfish)
├── playbooks/            site-common, sre-toolchain, local-inference, redfish-oob
├── inventories/          production, staging, development (hosts, group_vars, host_vars)
├── group_vars/all.yml
├── docs/                 7 ADRs, compliance-controls.yml, controls/ evidence/ schemas/ policies/ examples/
├── scripts/              validate-compliance-controls.py, export-compliance-posture.py,
│                         galaxy-sbom.py, ai-compliance-review.py, check-vault-encrypted.sh
└── .github/workflows/    ci.yml, ai-compliance-review.yml
```

Roles: `aide apparmor auditd common dns fail2ban kernel_lockdown
log_forwarding nftables_egress ntp ollama redfish rkhunter rsyslog_hardening
sre_toolchain ssh_hardening systemd_hardening ufw usbguard users vector
wazuh_agent`.

## File inventory

| Metric | Value |
|--------|-------|
| Tracked files | 243 |
| Roles | 22 |
| Playbooks | 4 |
| `.yml` files | 138 |
| ADRs | 7 (ADR-001..007) |
| Compliance controls / policies | 3 controls (CTL-001..003), 5 policies (POL-001..005) |

## Dependency / toolchain graph

Galaxy collections (`requirements.yml`, exact pins):

| Collection | Version | Note |
|------------|---------|------|
| `ansible.posix` | `2.2.0` | exact pin |
| `community.general` | `13.0.1` | exact pin |

Both installed cleanly this session via `ansible-galaxy` into the gitignored
`collections/` (ADR-001 F4.2 deterministic set). A CycloneDX SBOM of the
resolved set is generated in CI (`scripts/galaxy-sbom.py`).

Dev toolchain (`requirements-dev.txt`, exact pins, Renovate-managed):
`ansible-core==2.21.0`, `ansible-lint==26.4.0`, `yamllint==1.38.0`,
`pre-commit==4.6.0`, `PyYAML==6.0.3`, `jsonschema==4.26.0`.

## CI configuration

`.github/workflows/ci.yml`, `permissions: contents: read`, `concurrency` with
`cancel-in-progress`. Jobs:

| Job | What it runs |
|-----|--------------|
| `lint` | yamllint + ansible-lint (production profile) |
| `syntax-check` | `ansible-playbook --syntax-check` per playbook |
| `validate-compliance` | compliance schema/role validator + posture export smoke test |
| `vault-example` | proves `docs/examples/vault.yml` decrypts with the throwaway password |
| `collections-sbom` | CycloneDX SBOM artifact |
| `molecule` (matrix x4) | `molecule test` for users, ssh_hardening, auditd, common (noble + resolute) |
| `pre-commit` | hygiene hooks (yamllint/ansible-lint skipped; dedicated job above) |
| `secret-scan` | gitleaks `dir` over the working tree (vendored `collections/` excluded) |

A second workflow `ai-compliance-review.yml` runs an AI-in-CI compliance review
via local inference (ADR-006). All `uses:` are SHA-pinned with version comments.

## Toolchain available in this environment

| Tool | Version | Note |
|------|---------|------|
| ansible-lint | 26.4.0 | matches the CI pin |
| ansible-core | 2.19.10 (installed this session) | CI pins **2.21.0**; minor delta noted in 01-baseline `[UNVERIFIED]` |
| yamllint | present | clean |
| gitleaks | dev build (`detect`) | CI uses v8.30.1 (`dir`) |
| python3 | 3.11.15 | runs the compliance validators |

Absent: `molecule` and Docker (the Molecule matrix cannot run here — recorded
as a baseline gap, not a defect).
