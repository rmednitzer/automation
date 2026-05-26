# automation

Ansible automation for the fleet — system hardening, configuration
management, operator-host tooling — aligned with EU and Austrian
regulatory requirements.

Companions:
[`infra`](https://github.com/rmednitzer/infra) (OpenTofu provisioning),
[`runbooks`](https://github.com/rmednitzer/runbooks) (ad-hoc operator
scripts).

## Regulatory scope

| Framework | Coverage |
|-----------|----------|
| NIS2 Directive (EU 2022/2555) | Art 20–23: risk management, incident handling, reporting |
| NISG 2026 (Austrian transposition) | National NIS2 implementation; effective 2026-10-01 |
| Cyber Resilience Act (EU 2024/2847) | Annex I: secure-by-design, minimal attack surface |
| GDPR (EU 2016/679) / Austrian DSG | Art 5, 25, 32: data protection by design |
| ISO/IEC 27001:2022 | Annex A controls (A.5–A.8) |

Controls and policies live in
[`docs/compliance-controls.yml`](docs/compliance-controls.yml) and map
to the regulatory frameworks above.

## Getting started

### Prerequisites

- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/) ≥ 2.15
- Python ≥ 3.10

### Setup

```bash
ansible-galaxy install -r requirements.yml
```

### Usage

```bash
# Dry-run
ansible-playbook -i inventories/<env>/hosts playbooks/site-common.yml --check --diff

# Apply
ansible-playbook -i inventories/<env>/hosts playbooks/site-common.yml

# Compliance-tagged roles only
ansible-playbook -i inventories/<env>/hosts playbooks/site-common.yml --tags compliance

# Specific roles
ansible-playbook -i inventories/<env>/hosts playbooks/site-common.yml --tags ssh,firewall,audit
```

## Roles

| Role | Purpose | Key compliance references |
|------|---------|---------------------------|
| `common` | Base packages, timezone, sysctl, kernel/FS hardening, log retention | CTL-002, CTL-003, POL-004, NIS2 Art 21.2(a)(e), GDPR Art 25/32, CRA Annex I |
| `users` | User accounts, sudo, password policy, account lockout | CTL-001, POL-001, POL-003, NIS2 Art 21.2(i), GDPR Art 32 |
| `ntp` | `chrony` time sync (Austrian/EU NTP pools, NTS) | CTL-003, POL-002, POL-003, ISO 27001 A.8.17 |
| `ssh_hardening` | SSH server hardening, legal banner, BSI-aligned crypto | CTL-001, POL-001, POL-003, NIS2 Art 21.2(h)(i) |
| `ufw` | UFW firewall, default-deny, IPv6, rate limiting | POL-001, NIS2 Art 21.2(e), GDPR Art 32 |
| `fail2ban` | Intrusion prevention with `recidive` jail | POL-002, NIS2 Art 21.2(b) |
| `aide` | File integrity monitoring | CTL-002, POL-002, POL-003, NIS2 Art 21.2(a), GDPR Art 32 |
| `rkhunter` | Rootkit detection (hidden procs, kernel modules, signatures) | POL-002, NIS2 Art 21.2(a)(b), GDPR Art 32, ISO 27001 A.8.7 |
| `log_forwarding` | Central log forwarding via rsyslog (TLS) + `audisp-remote` | CTL-002, CTL-003, POL-002, POL-003, NIS2 Art 21.2(a), GDPR Art 5(2) |
| `auditd` | System audit logging (CIS + NIS2/GDPR rules) | CTL-002, CTL-003, POL-004, POL-005, GDPR Art 5(2), NIS2 Art 21.2(a) |
| `sre_toolchain` | SRE/Platform/Security toolchain installer (kind, flux, trivy, sops, cosign, opa, k6, …) for operator hosts | NIS2 Art 21.2(a)(e), CRA Annex I, ISO 27001 A.8.30, POL-002, CTL-002 |

The first ten roles form the fleet hardening baseline applied by
`playbooks/site-common.yml`. `sre_toolchain` targets operator hosts
only (workstations, admin/bastion VMs, CI runners) via
`playbooks/sre-toolchain.yml`.

## Repository structure

```
inventories/<env>/    # production, staging, development (each with own group_vars, host_vars)
playbooks/            # Top-level playbooks (site-common, sre-toolchain)
roles/                # Custom roles (see table above)
group_vars/all.yml    # Global group variables
docs/                 # Compliance controls catalog + ADRs
scripts/              # Local helpers (compliance-controls validator)
```

Files and templates live **inside** each role
(`roles/<role>/files/`, `roles/<role>/templates/`) — not at the
repository root, per the
[official Ansible sample setup](https://docs.ansible.com/ansible/latest/tips_tricks/sample_setup.html).

## Evidence and audit

Each role produces configuration artifacts that serve as compliance
evidence:

- **Audit logs** (`/var/log/audit/`) — CIS + NIS2/GDPR rules, immutable
- **AIDE reports** (`/var/log/aide/`) — daily file-integrity checks
- **rkhunter reports** (`/var/log/rkhunter.log`) — daily rootkit scans
- **Auth logs** — retained per `common_log_retention.security_audit`
  (365 days default)
- **SSH banner** — legal monitoring notice (GDPR Art 5(2))
- **Sysctl hardening** — kernel security parameters per CRA Annex I

Log retention tiers (CTL-002 evidence retention; see
`docs/compliance-controls.yml`):

| Tier | Days |
|------|------|
| `governance` | 3650 (10 years) |
| `incidents` | 1825 (5 years) |
| `dr_tests` | 1825 (5 years) |
| `ci` | 1095 (3 years) |
| `security_audit` | 365 (1 year) |
| `operational` | 90 |

## Validation and audit records

Periodic full-tree validation against known-good sources (CIS Ubuntu
Benchmark, BSI TR-02102-4, upstream OpenSSH / chrony / auditd /
`pam_faillock` / `pam_pwquality` manuals, Ansible production-profile
lint rules). Each pass produces an ADR under [`docs/`](docs/):

| ADR | Date | Topic |
|-----|------|-------|
| [ADR-001](docs/ADR-001-code-validation-baseline.md) | 2026-05-24 | Code validation baseline — index, findings, accepted design tensions, doc-parity policy |

Static analysis is enforced on every push and pull request by
[`.github/workflows/ci.yml`](.github/workflows/ci.yml):

```bash
# Reproduce locally
make install   # ansible-core, ansible-lint, yamllint, pre-commit, galaxy deps
make check     # lint + syntax-check + validate-compliance
```

`make check` runs:

| Check | Tool | Purpose |
|-------|------|---------|
| `yamllint` | yamllint + project overrides (`.yamllint`) | YAML hygiene |
| `ansible-lint` | production profile (FQCN, `no-changed-when` enforced) | Ansible conformance |
| `ansible-playbook --syntax-check` | per playbook | Playbook syntax |
| `scripts/validate-compliance-controls.py` | local Python check | `docs/compliance-controls.yml` schema and role cross-references |
| `pre-commit run --all-files` | pre-commit | EditorConfig, EOF, trailing whitespace, private-key detection, hygiene |

ADR-001's current baseline records `0 failure(s), 0 warning(s)` under
`ansible-lint production` and `yamllint` with project overrides.

## Governance

| File | Purpose |
|------|---------|
| [`CLAUDE.md`](./CLAUDE.md) | Conventions, FQCN policy, variable precedence |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Workflow, compliance-controls obligation |
| [`CHANGELOG.md`](./CHANGELOG.md) | Keep a Changelog 1.1.0; cite CTL-/POL- IDs |
| [`LIMITATIONS.md`](./LIMITATIONS.md) | Known scope boundaries (L1–L7) |
| [`Makefile`](./Makefile) | `make help` for local targets |
| [`docs/compliance-controls.yml`](./docs/compliance-controls.yml) | Audit-facing CTL-/POL- catalog |
| [`.github/SECURITY.md`](./.github/SECURITY.md) | Vulnerability reporting |
| [`.github/PULL_REQUEST_TEMPLATE.md`](./.github/PULL_REQUEST_TEMPLATE.md) | PR checklist |
| [`.github/CODEOWNERS`](./.github/CODEOWNERS) | Review assignment |
| [`LICENSE`](./LICENSE) / [`NOTICE`](./NOTICE) | Apache 2.0 |
