# automation

Ansible automation for the fleet — system hardening, configuration management, and operator-host tooling — aligned with EU and Austrian regulatory requirements.

Companion repositories: [`infra`](https://github.com/rmednitzer/infra) (OpenTofu provisioning) and [`runbooks`](https://github.com/rmednitzer/runbooks) (ad-hoc operator scripts).

## Regulatory Scope

This repository enforces technical controls required by:

| Framework | Scope |
|-----------|-------|
| NIS2 Directive (EU 2022/2555) | Art 20–23: risk management, incident handling, reporting |
| NISG 2026 (Austrian transposition) | National NIS2 implementation, effective 2026-10-01 |
| Cyber Resilience Act (EU 2024/2847) | Annex I: secure-by-design, minimal attack surface |
| GDPR (EU 2016/679) / Austrian DSG | Art 5, 25, 32: data protection by design, security of processing |
| ISO/IEC 27001:2022 | Annex A controls (A.5–A.8) |

Controls and policies are defined in [`docs/compliance-controls.yml`](docs/compliance-controls.yml) and mapped to the regulatory frameworks above.

## Getting Started

### Prerequisites

- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/) >= 2.15
- Python >= 3.10

### Setup

```bash
# Install Galaxy dependencies
ansible-galaxy install -r requirements.yml
```

### Usage

```bash
# Dry-run a playbook
ansible-playbook -i inventories/<env>/hosts playbooks/site-common.yml --check --diff

# Run a playbook
ansible-playbook -i inventories/<env>/hosts playbooks/site-common.yml

# Run only compliance-tagged roles
ansible-playbook -i inventories/<env>/hosts playbooks/site-common.yml --tags compliance

# Run specific roles
ansible-playbook -i inventories/<env>/hosts playbooks/site-common.yml --tags ssh,firewall,audit
```

## Roles

| Role | Purpose | Key Compliance References |
|------|---------|---------------------------|
| `common` | Base packages, timezone, sysctl, kernel/FS hardening, log retention | CTL-002, CTL-003, POL-004, NIS2 Art 21.2(a)(e), GDPR Art 25/32, CRA Annex I |
| `users` | User accounts, sudo, password policy, account lockout | CTL-001, POL-001, POL-003, NIS2 Art 21.2(i), GDPR Art 32 |
| `ntp` | Chrony time synchronisation (Austrian/EU NTP pools, NTS) | CTL-003, POL-002, POL-003, ISO 27001 A.8.17 |
| `ssh_hardening` | SSH server hardening, legal banner, approved ciphers | CTL-001, POL-001, POL-003, NIS2 Art 21.2(h)(i) |
| `ufw` | UFW firewall with default-deny, IPv6, rate limiting | POL-001, NIS2 Art 21.2(e), GDPR Art 32 |
| `fail2ban` | Intrusion prevention with recidive jail | POL-002, NIS2 Art 21.2(b) |
| `aide` | File integrity monitoring (AIDE) | CTL-002, POL-002, POL-003, NIS2 Art 21.2(a), GDPR Art 32 |
| `rkhunter` | Rootkit detection (hidden processes, kernel modules, signatures) | POL-002, NIS2 Art 21.2(a)(b), GDPR Art 32, ISO 27001 A.8.7 |
| `log_forwarding` | Centralised log forwarding via rsyslog (TLS) | CTL-002, CTL-003, POL-002, POL-003, NIS2 Art 21.2(a), GDPR Art 5(2) |
| `auditd` | System audit logging (CIS + NIS2/GDPR rules) | CTL-002, CTL-003, POL-004, POL-005, GDPR Art 5(2), NIS2 Art 21.2(a) |
| `sre_toolchain` | SRE/Platform/Security toolchain installer (kind, flux, trivy, sops, cosign, opa, k6, …) for operator hosts | NIS2 Art 21.2(a)(e), CRA Annex I, ISO 27001 A.8.30, POL-002, CTL-002 |

The first ten roles are the fleet hardening baseline applied by `playbooks/site-common.yml`. `sre_toolchain` targets operator hosts only (workstations, admin/bastion, CI runners) and ships its own playbook at `playbooks/sre-toolchain.yml`.

## Repository Structure

```
inventories/          Per-environment inventory (production, staging, development)
                      with per-env group_vars/ and host_vars/
playbooks/            Top-level playbooks
roles/                Custom Ansible roles (see Roles table above)
group_vars/all.yml    Global group variables
docs/                 Compliance controls catalog + ADRs
scripts/              Local helper scripts (compliance-controls validator)
```

## Evidence and Audit

Each role produces configuration artifacts that serve as compliance evidence:

- **Audit logs** (`/var/log/audit/`) — CIS + NIS2/GDPR rules, immutable
- **AIDE reports** (`/var/log/aide/`) — daily file integrity checks
- **rkhunter reports** (`/var/log/rkhunter.log`) — daily rootkit scans
- **Auth logs** — retained per `common_log_retention.security_audit` (365 days default)
- **SSH banner** — legal monitoring notice per GDPR Art 5(2)
- **Sysctl hardening** — kernel security parameters per CRA Annex I

Log retention tiers are aligned with CTL-002 evidence retention requirements (see `docs/compliance-controls.yml`):
- `governance`: 10 years (3650 days)
- `incidents`: 5 years (1825 days)
- `ci`: 3 years (1095 days)
- `dr_tests`: 5 years (1825 days)
- `security_audit`: 1 year (365 days)
- `operational`: 90 days

## Validation and Audit Records

The codebase is periodically validated end-to-end against known-good
sources (CIS Ubuntu Benchmark, BSI TR-02102-4, upstream OpenSSH /
chrony / auditd / `pam_faillock` / `pam_pwquality` manuals, Ansible
production-profile lint rules). Each pass produces an Architectural
Decision Record under [`docs/`](docs/):

| ADR | Date | Topic |
|-----|------|-------|
| [ADR-001](docs/ADR-001-code-validation-baseline.md) | 2026-05-24 | Code validation baseline — full index, findings, accepted design tensions, doc-parity policy |

Static analysis is also enforced on every push and pull request by
[`.github/workflows/ci.yml`](.github/workflows/ci.yml):

```bash
# Reproduce locally
make install   # ansible-core, ansible-lint, yamllint, pre-commit, galaxy deps
make check     # lint + syntax-check + validate-compliance
```

`make check` runs:

| Check | Tool | Purpose |
|-------|------|---------|
| `yamllint` | yamllint with project overrides (`.yamllint`) | YAML hygiene |
| `ansible-lint` | production profile (FQCN, `no-changed-when` enforced) | Ansible conformance |
| `ansible-playbook --syntax-check` | per playbook | Playbook syntax |
| `scripts/validate-compliance-controls.py` | local Python check | `docs/compliance-controls.yml` schema and role cross-references |
| `pre-commit run --all-files` | pre-commit | EditorConfig, end-of-file, trailing whitespace, private-key detection, hygiene |

The current baseline (ADR-001) records `0 failure(s), 0 warning(s)`
under `ansible-lint` profile `production` and `yamllint` with project
overrides.

## Governance

| File | Purpose |
|------|---------|
| [`CLAUDE.md`](./CLAUDE.md) | Conventions, FQCN policy, variable precedence |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Workflow, compliance-controls obligation |
| [`CHANGELOG.md`](./CHANGELOG.md) | Keep a Changelog 1.1.0; cite CTL- / POL- IDs |
| [`LIMITATIONS.md`](./LIMITATIONS.md) | Known scope boundaries (L1–L7) |
| [`Makefile`](./Makefile) | `make help` for local targets |
| [`docs/compliance-controls.yml`](./docs/compliance-controls.yml) | Audit-facing CTL- / POL- catalog |
| [`.github/SECURITY.md`](./.github/SECURITY.md) | Vulnerability reporting |
| [`.github/PULL_REQUEST_TEMPLATE.md`](./.github/PULL_REQUEST_TEMPLATE.md) | PR checklist |
| [`.github/CODEOWNERS`](./.github/CODEOWNERS) | Review assignment |
| [`LICENSE`](./LICENSE) / [`NOTICE`](./NOTICE) | Apache 2.0 |
